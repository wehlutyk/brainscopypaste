import os
from tempfile import mkstemp
from datetime import timedelta

import pytest
import networkx as nx

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote
from brainscopypaste.load import MemeTrackerParser, FAFeatureLoader


# Quotes and urls are intentionally not ordered to check for ordering later on.
content = '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>


2\t5\thate that i love you so\t36543
\t2\t2\tthat i love you\t950238
\t\t2008-09-13 14:45:39\t1\tM\tsome-url-3
\t\t2008-09-17 04:09:03\t1\tB\tsome-url-4

\t3\t2\ti love you\t43
\t\t2008-08-01 00:24:08\t1\tM\tsome-url-2
\t\t2008-08-01 00:00:16\t2\tB\tsome-url-with-"-and-'-1

1\t3\tyes we can yes we can\t43112
\t3\t2\tyes we can\t1485
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


@pytest.fixture
def memetracker_file():
    fd, filepath = mkstemp()

    def fin():
        os.remove(filepath)

    with open(fd, 'w') as tmp:
        tmp.write(content)

    line_count = content.count('\n') + 1
    return filepath, line_count


@pytest.fixture(params=contents_errored.keys())
def memetracker_file_errored(request):
    fd, filepath = mkstemp()

    def fin():
        os.remove(filepath)

    with open(fd, 'w') as tmp:
        tmp.write(contents_errored[request.param])

    line_count = contents_errored[request.param].count('\n') + 1
    return request.param, filepath, line_count


def assert_loaded():
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

        assert q4.string == 'i love you'
        assert q9.string == 'that i love you'
        assert q1.string == 'yes we can'
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


def test_parser(tmpdb, memetracker_file):
    filepath, line_count = memetracker_file
    MemeTrackerParser(filepath, line_count=line_count).parse()
    assert_loaded()


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
    loader = FAFeatureLoader()
    # No 0 pagerank.
    for v in loader.pagerank().values():
        assert v > 0
    # Test values on a small graph.
    # Weights are used as strengths, not costs, and the graph is directed.
    loader._norms_graph = nx.DiGraph()
    loader._norms_graph.add_weighted_edges_from([(1, 3, .5), (2, 3, .5),
                                                 (3, 4, .5), (3, 5, .5),
                                                 (1, 4, 2), (4, 1, 1)])
    reference = {1: 0.343157577741676,
                 2: 0.04913541630116447,
                 3: 0.14923730837323892,
                 4: 0.34590842522412957,
                 5: 0.11256127235979119}
    for k, v in loader.pagerank().items():
        assert abs(reference[k] - v) < 1e-15


def test_fa_feature_loader_betweenness():
    loader = FAFeatureLoader()
    # Test values on a small graph.
    loader._norms_graph = nx.DiGraph()
    loader._norms_graph.add_weighted_edges_from([(1, 2, 1), (1, 3, 1),
                                                 (2, 4, 1), (3, 4, 2)])
    # There are no 0 betweennesses.
    # Weights are used as strengths, not costs, and the graph is directed.
    assert loader.betweenness() == {3: 1/6}


def test_fa_feature_loader_clustering():
    # Test values on a small graph.
    # Weights are used as strengths, not costs, and the graph is undirected.
    loader = FAFeatureLoader()
    loader._norms_graph = nx.DiGraph()
    loader._norms_graph.add_weighted_edges_from([(1, 2, 1), (1, 3, 1),
                                                 (3, 2, 1), (3, 4, 1),
                                                 (4, 5, 1), (3, 5, 1),
                                                 (5, 3, 1)])
    assert loader.clustering() == {1: 0.5,
                                   2: 0.5,
                                   3: 0.18832675415790612,
                                   4: 0.6299605249474366,
                                   5: 0.6299605249474366}
    # On the full dataset, there are no 0 clusterings.
    loader = FAFeatureLoader()
    for v in loader.clustering().values():
        assert v > 0
