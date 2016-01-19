import os
from tempfile import mkstemp

import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote, Url
from brainscopypaste.load.memetracker import MemeTrackerParser


test_memetracker_content = '''format:
<ClSz>	<TotFq>	<Root>	<ClusterId>
	<QtFq>	<Urls>	<QtStr>	<QuteId>
	<Tm>	<Fq>	<UrlTy>	<Url>


4	24898	hate that i love you so	36543
	23785	20305	i love you	43
		2008-08-01 00:00:16	2	B	some-url-1
		2008-08-01 00:24:08	1	M	some-url-2

	6	6	that i love you	950238
		2008-09-13 14:45:39	1	M	some-url-3
		2008-09-17 04:09:03	1	B	some-url-4

8	21720	yes we can yes we can	43112
	21041	18574	yes we can	1485
		2008-08-01 00:12:05	1	B	some-url-5
		2008-08-01 00:31:56	2	M	some-url-6'''


@pytest.fixture
def memetracker_file():
    tmp, filepath = mkstemp()
    tmp = os.fdopen(tmp, 'w')

    def fin():
        os.remove(filepath)

    tmp.write(test_memetracker_content)
    tmp.close()
    return filepath


def test_parser(tmpdb, memetracker_file):
    n_lines = test_memetracker_content.count('\n') + 1
    MemeTrackerParser(memetracker_file).parse(limitlines=n_lines)

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
