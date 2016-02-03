import os
from tempfile import mkstemp
from datetime import timedelta

import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote
from brainscopypaste.load import MemeTrackerParser


# Quotes and urls are intentionally not ordered to check for ordering later on.
content = '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

	3	2	i love you	43
		2008-08-01 00:24:08	1	M	some-url-2
		2008-08-01 00:00:16	2	B	some-url-with-"-and-'-1

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:31:56	2	M	some-url-6
		2008-08-01 00:12:05	1	B	some-url-5'''


contents_errored = {
    'Cluster size #43112': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-with-"-and-'-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

2	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Cluster frequency #36543': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	10	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-with-"-and-'-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Quote size #950238': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-with-"-and-'-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	4	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Quote frequency #1485': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-with-"-and-'-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	4	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6'''
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
