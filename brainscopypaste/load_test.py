import os
from tempfile import mkstemp
from datetime import timedelta
import pickle

import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote
from brainscopypaste.load import (MemeTrackerParser, FAFeatureLoader,
                                  load_fa_features,
                                  load_mt_frequency_and_tokens)
from brainscopypaste.filter import filter_clusters
from brainscopypaste.conf import settings


# Quotes and urls are intentionally not ordered to check for ordering later on.
content = '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t5\thate that i love you so\t36543
\t2\t2\tyes that's what love is\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

\t3\t2\tyes that person does love you\t43
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1

1\t3\tyes we can yes we can\t43112
\t3\t2\tyes we can do this\t1485
\t\t2008-08-01 00:31:56\t2\tM\tsome-url-6
\t\t2008-08-01 00:12:05\t1\tB\tsome-url-5'''


contents_errored = {
    'Cluster size #43112': '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t5\thate that i love you so\t36543
\t3\t2\ti love you\t43
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2

\t2\t2\tthat i love you\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

2\t3\tyes we can yes we can\t43112
\t3\t2\tyes we can\t1485
\t\t2008-08-01 00:12:05\t1\tB\tsome-url-5
\t\t2008-08-01 00:31:56\t2\tM\tsome-url-6''',
    'Cluster frequency #36543': '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t10\thate that i love you so\t36543
\t3\t2\ti love you\t43
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2

\t2\t2\tthat i love you\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

1\t3\tyes we can yes we can\t43112
\t3\t2\tyes we can\t1485
\t\t2008-08-01 00:12:05\t1\tB\tsome-url-5
\t\t2008-08-01 00:31:56\t2\tM\tsome-url-6''',
    'Quote size #950238': '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t5\thate that i love you so\t36543
\t3\t2\ti love you\t43
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2

\t2\t4\tthat i love you\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

1\t3\tyes we can yes we can\t43112
\t3\t2\tyes we can\t1485
\t\t2008-08-01 00:12:05\t1\tB\tsome-url-5
\t\t2008-08-01 00:31:56\t2\tM\tsome-url-6''',
    'Quote frequency #1485': '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t5\thate that i love you so\t36543
\t3\t2\ti love you\t43
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2

\t2\t2\tthat i love you\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

1\t3\tyes we can yes we can\t43112
\t4\t2\tyes we can\t1485
\t\t2008-08-01 00:12:05\t1\tB\tsome-url-5
\t\t2008-08-01 00:31:56\t2\tM\tsome-url-6'''
}


@pytest.yield_fixture
def memetracker_file():
    fd, filepath = mkstemp()
    with open(fd, 'w') as tmp:
        tmp.write(content)

    line_count = content.count('\n') + 1
    yield filepath, line_count
    os.remove(filepath)


@pytest.yield_fixture(params=contents_errored.keys())
def memetracker_file_errored(request):
    fd, filepath = mkstemp()
    with open(fd, 'w') as tmp:
        tmp.write(contents_errored[request.param])

    line_count = contents_errored[request.param].count('\n') + 1
    yield request.param, filepath, line_count
    os.remove(filepath)


def test_parser(tmpdb, memetracker_file):
    filepath, line_count = memetracker_file
    MemeTrackerParser(filepath, line_count=line_count).parse()

    with session_scope() as session:
        assert session.query(Cluster).count() == 2
        assert session.query(Quote).count() == 3

        c3 = session.query(Cluster).filter_by(sid=36543).one()
        c4 = session.query(Cluster).filter_by(sid=43112).one()
        q4 = session.query(Quote).filter_by(sid=43).one()
        q9 = session.query(Quote).filter_by(sid=950238).one()
        q1 = session.query(Quote).filter_by(sid=1485).one()

        assert set(c3.quotes.all()) == set([q4, q9])
        assert c4.quotes.all() == [q1]
        assert c3.size == 2
        assert c4.size == 1
        assert c3.size_urls == 4
        assert c4.size_urls == 2
        assert c3.frequency == 5
        assert c4.frequency == 3
        assert c3.urls[0].timestamp.second == 16
        assert c3.urls[0].frequency == 2
        assert c3.urls[0].url_type == 'B'
        assert c3.urls[0].url == 'some-url-with-"-and-\'-1'
        assert abs(c3.span - timedelta(days=47)) < timedelta(hours=5)

        assert q4.string == "yes that person does love you"
        assert q9.string == "yes that's what love is"
        assert q1.string == 'yes we can do this'
        assert q4.size == 2
        assert q9.size == 2
        assert q1.size == 2
        assert q4.frequency == 3
        assert q9.frequency == 2
        assert q1.frequency == 3
        assert q4.span == timedelta(minutes=23, seconds=52)

        assert q4.urls[0].timestamp.second == 16
        assert q4.urls[0].frequency == 2
        assert q4.urls[0].url_type == 'B'
        assert q4.urls[0].url == 'some-url-with-"-and-\'-1'

        assert q9.urls[1].timestamp.second == 3
        assert q9.urls[1].frequency == 1
        assert q9.urls[1].url_type == 'B'
        assert q9.urls[1].url == 'some-url-4'

        assert q1.urls[1].timestamp.second == 56
        assert q1.urls[1].frequency == 2
        assert q1.urls[1].url_type == 'M'
        assert q1.urls[1].url == 'some-url-6'


def test_parser_errored(tmpdb, memetracker_file_errored):
    error, filepath, line_count = memetracker_file_errored
    with pytest.raises(ValueError) as excinfo:
        MemeTrackerParser(filepath, line_count=line_count).parse()
    assert error in str(excinfo.value)


def test_fa_feature_loader_norms():
    loader = FAFeatureLoader()
    norms = loader._norms
    # The loading is cached.
    assert norms is loader._norms
    # Test a few values.
    assert norms['abdomen'] == [('stomach', True, .566),
                                ('body', True, .072),
                                ('muscle', True, .046),
                                ('sit ups', False, .026),
                                ('organ', True, .02),
                                ('pain', True, .02),
                                ('belly', True, .013),
                                ('cramp', True, .013),
                                ('crunches', False, .013),
                                ('intestine', True, .013),
                                ('sex', True, .013),
                                ('six pack', False, .013)]
    assert norms['galoshes'] == [('rain', True, .307),
                                 ('boots', True, .244),
                                 ('wet', True, .102),
                                 ('shoe', True, .087),
                                 ('snow', True, .071),
                                 ('rubber', True, .063),
                                 ('mud', True, .024)]


def test_fa_feature_loader_norms_graph():
    loader = FAFeatureLoader()
    graph = loader._norms_graph
    # The loading is cached.
    assert graph is loader._norms_graph
    # Test a few values.
    assert graph.edge['abdomen'] == {'stomach': {'weight': .566},
                                     'body': {'weight': .072},
                                     'muscle': {'weight': .046},
                                     'sit ups': {'weight': .026},
                                     'organ': {'weight': .02},
                                     'pain': {'weight': .02},
                                     'belly': {'weight': .013},
                                     'cramp': {'weight': .013},
                                     'crunches': {'weight': .013},
                                     'intestine': {'weight': .013},
                                     'sex': {'weight': .013},
                                     'six pack': {'weight': .013}}
    # There are no edges with 0 weight
    for u, v, weight in graph.edges_iter(data='weight'):
        assert weight > 0


def test_fa_feature_loader_inverse_norms_graph():
    loader = FAFeatureLoader()
    graph = loader._inverse_norms_graph
    # The loading is cached.
    assert graph is loader._inverse_norms_graph
    # Test a few values.
    assert graph.edge['abdomen'] == {'stomach': {'weight': 1 / .566},
                                     'body': {'weight': 1 / .072},
                                     'muscle': {'weight': 1 / .046},
                                     'sit ups': {'weight': 1 / .026},
                                     'organ': {'weight': 1 / .02},
                                     'pain': {'weight': 1 / .02},
                                     'belly': {'weight': 1 / .013},
                                     'cramp': {'weight': 1 / .013},
                                     'crunches': {'weight': 1 / .013},
                                     'intestine': {'weight': 1 / .013},
                                     'sex': {'weight': 1 / .013},
                                     'six pack': {'weight': 1 / .013}}
    # There are no edges with 0 weight
    for u, v, weight in graph.edges_iter(data='weight'):
        assert weight > 0


def test_fa_feature_loader_undirected_norms_graph():
    loader = FAFeatureLoader()
    graph = loader._undirected_norms_graph
    # The loading is cached.
    assert graph is loader._undirected_norms_graph
    # Test a few values.
    assert graph.edge['abdomen'] == {'stomach': {'weight': .566 + .021},
                                     'body': {'weight': .072},
                                     'muscle': {'weight': .046},
                                     'sit ups': {'weight': .026},
                                     'organ': {'weight': .02},
                                     'pain': {'weight': .02},
                                     'belly': {'weight': .013},
                                     'cramp': {'weight': .013},
                                     'crunches': {'weight': .013},
                                     'intestine': {'weight': .013},
                                     'sex': {'weight': .013},
                                     'six pack': {'weight': .013}}
    # There are no edges with 0 weight.
    for u, v, weight in graph.edges_iter(data='weight'):
        assert weight > 0


def test_fa_feature_loader_remove_zeros():
    testdict = {'a': -1, 'b': 0, 'c': .1, 'd': 1, 'e': 'something',
                'f': 0, 0: 1}
    FAFeatureLoader._remove_zeros(testdict)
    assert testdict == {'a': -1, 'c': .1, 'd': 1, 'e': 'something', 0: 1}


def test_fa_feature_loader_degree():
    loader = FAFeatureLoader()
    degree = loader.degree()
    graph = loader._norms_graph
    # Test a few values. Weights are ignored, graph is directed.
    assert degree['abdomen'] == 1 / (len(graph) - 1)
    assert degree['speaker'] == 9 / (len(graph) - 1)
    # No 0 degree.
    for v in degree.values():
        assert v > 0


def test_fa_feature_loader_pagerank():
    # No 0 pagerank.
    for v in FAFeatureLoader().pagerank().values():
        assert v > 0


# No tests are made on the full FA betweenness because it takes 15 min
# to compute. Instead, test are made with a toy FA source file below.


def test_fa_feature_loader_clustering():
    # No 0 clustering.
    for v in FAFeatureLoader().clustering().values():
        assert v > 0


fa_header = '''<HTML>
<BODY>
<PRE>
CUE, TARGET, NORMED?, #G, #P, FSG
'''


fa_footer = '''
</pre>
</BODY>
</HTML>'''

fa_cases = {
    'degree': {
        'content': '''a, b, x, x, x, .5
b, c, x, x, x, .5
c, d, x, x, x, .5
c, e, x, x, x, .5
a, d, x, x, x, 2''',
        'result': {'b': 1/4, 'c': 1/4, 'd': 2/4, 'e': 1/4}
    },
    'pagerank': {
        'content': '''a, c, x, x, x, .5
b, c, x, x, x, .5
c, d, x, x, x, .5
c, e, x, x, x, .5
a, d, x, x, x, 2
d, a, x, x, x, 1''',
        'result': {'a': 0.343157577741676, 'b': 0.04913541630116447,
                   'c': 0.14923730837323892, 'd': 0.34590842522412957,
                   'e': 0.11256127235979119},
        'tol': 1e-15
    },
    'betweenness': {
        'content': '''a, b, x, x, x, 1
a, c, x, x, x, 1
b, d, x, x, x, 1
c, d, x, x, x, 2''',
        'result': {'c': 1/6}
    },
    'clustering': {
        'content': '''a, b, x, x, x, 1
a, c, x, x, x, 1
c, b, x, x, x, 1
c, d, x, x, x, 1
d, e, x, x, x, 1
c, e, x, x, x, 1
e, c, x, x, x, 1''',
        'result': {'a': 0.5, 'b': 0.5, 'c': 0.18832675415790612,
                   'd': 0.6299605249474366, 'e': 0.6299605249474366}
    }
}


@pytest.yield_fixture(params=fa_cases.keys())
def fa_sources(request):
    content = fa_cases[request.param]['content']
    expected_result = fa_cases[request.param]['result']
    tol = fa_cases[request.param].get('tol')

    # Create fake FA source.
    fd, fa_filepath = mkstemp()
    with open(fd, 'w') as tmp:
        tmp.write(fa_header + content + fa_footer)

    # Run the test.
    with settings.override(('FA_SOURCES', [fa_filepath])):
        yield request.param, expected_result, tol

    # Clean up.
    os.remove(fa_filepath)


def test_fa_feature_loader_feature(fa_sources):
    feature, expected_result, tol = fa_sources
    result = getattr(FAFeatureLoader(), feature)()
    if tol is None:
        assert result == expected_result
    else:
        assert set(result.keys()) == set(expected_result.keys())
        for k, v in expected_result.items():
            assert abs(result[k] - v) < tol


def test_load_fa_features(fa_sources):
    feature, expected_result, tol = fa_sources
    with settings.file_override('DEGREE', 'PAGERANK',
                                'BETWEENNESS', 'CLUSTERING'):
        load_fa_features()
        with open(getattr(settings, feature.upper()), 'rb') as f:
            result = pickle.load(f)
        if tol is None:
            assert result == expected_result
        else:
            assert set(result.keys()) == set(expected_result.keys())
            for k, v in expected_result.items():
                assert abs(result[k] - v) < tol


def test_load_mt_frequency_and_tokens(tmpdb, memetracker_file):
    filepath, line_count = memetracker_file
    MemeTrackerParser(filepath, line_count=line_count).parse()

    with pytest.raises(Exception) as excinfo:
        load_mt_frequency_and_tokens()
    assert 'no filtered quotes' in str(excinfo.value)

    # Run the filtering and test real values.
    filter_clusters()
    with settings.file_override('FREQUENCY', 'TOKENS'):
        load_mt_frequency_and_tokens()
        with open(settings.FREQUENCY, 'rb') as f:
            frequency = pickle.load(f)
        assert frequency == {'yes': 8, 'that': 5, 'be': 4, 'what': 2,
                             'love': 5, 'person': 3, 'do': 6, 'you': 3,
                             'we': 3, 'can': 3, 'this': 3}
        with open(settings.TOKENS, 'rb') as f:
            tokens = pickle.load(f)
        assert tokens == {'yes', 'that', "'s", 'what', 'love', 'is', 'person',
                          'does', 'you', 'we', 'can', 'do', 'this'}
