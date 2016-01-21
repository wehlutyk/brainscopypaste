import os
from tempfile import mkstemp

import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote, Url
from brainscopypaste.load.memetracker import MemeTrackerParser


content = '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6'''


contents_errored = {
    'Cluster size #36543': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


4	5	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Cluster frequency #36543': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	10	hate that i love you so	36543
	3	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Quote size #43': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	3	4	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6''',
    'Quote frequency #43': '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


2	5	hate that i love you so	36543
	5	2	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	2	2	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

1	3	yes we can yes we can	43112
	3	2	yes we can	1485
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

    return filepath


@pytest.fixture(params=contents_errored.keys())
def memetracker_file_errored(request):
    fd, filepath = mkstemp()

    def fin():
        os.remove(filepath)

    with open(fd, 'w') as tmp:
        tmp.write(contents_errored[request.param])

    return request.param, filepath


def assert_loaded():
    with session_scope() as session:
        assert session.query(Cluster).count() == 2
        assert session.query(Quote).count() == 3
        assert session.query(Url).count() == 6

        c3 = session.query(Cluster).get(36543)
        c4 = session.query(Cluster).get(43112)
        q4 = session.query(Quote).get(43)
        q9 = session.query(Quote).get(950238)
        q1 = session.query(Quote).get(1485)

        assert c3.quotes == [q4, q9]
        assert c4.quotes == [q1]
        assert c3.size == 2
        assert c4.size == 1
        assert c3.frequency == 5
        assert c4.frequency == 3

        assert q4.string == 'i love you'
        assert q9.string == 'that i love you'
        assert q1.string == 'yes we can'
        assert q4.frequency == 3
        assert q9.frequency == 2
        assert q1.frequency == 3

        assert q4.urls[0].timestamp.second == 16
        assert q4.urls[0].frequency == 2
        assert q4.urls[0].url_type == 'B'
        assert q4.urls[0].url == 'some-url-1'

        assert q9.urls[1].timestamp.second == 3
        assert q9.urls[1].frequency == 1
        assert q9.urls[1].url_type == 'B'
        assert q9.urls[1].url == 'some-url-4'

        assert q1.urls[1].timestamp.second == 56
        assert q1.urls[1].frequency == 2
        assert q1.urls[1].url_type == 'M'
        assert q1.urls[1].url == 'some-url-6'


def test_parser(tmpdb, memetracker_file):
    n_lines = content.count('\n') + 1
    MemeTrackerParser(memetracker_file, limitlines=n_lines).parse()
    assert_loaded()


def test_parser_errored(tmpdb, memetracker_file_errored):
    error, filepath = memetracker_file_errored
    n_lines = contents_errored[error].count('\n') + 1

    with pytest.raises(ValueError) as excinfo:
        MemeTrackerParser(filepath, limitlines=n_lines).parse()
    assert error in str(excinfo.value)


def test_parser_errored_ignored(tmpdb, memetracker_file_errored):
    error, filepath = memetracker_file_errored
    n_lines = contents_errored[error].count('\n') + 1
    MemeTrackerParser(filepath, limitlines=n_lines, nochecksums=True).parse()
    assert_loaded()
