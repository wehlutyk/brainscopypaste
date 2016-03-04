import os
from tempfile import mkstemp
from datetime import datetime
from itertools import product

import pytest

from brainscopypaste.load import MemeTrackerParser
from brainscopypaste.mine import Interval, Model, Time, Source, Past, Durl
from brainscopypaste.db import Quote
from brainscopypaste.utils import session_scope


def test_interval():
    interval = Interval(datetime(year=2008, month=1, day=1),
                        datetime(year=2008, month=2, day=5))
    assert datetime(year=2007, month=10, day=5) not in interval
    assert datetime(year=2007, month=12, day=31, hour=23) not in interval
    assert datetime(year=2008, month=1, day=1) in interval
    assert datetime(year=2008, month=1, day=15) in interval
    assert datetime(year=2008, month=2, day=4, hour=23) in interval
    assert datetime(year=2008, month=2, day=5) not in interval
    assert datetime(year=2008, month=2, day=6) not in interval
    assert datetime(year=2008, month=5, day=1) not in interval
    assert interval == Interval(datetime(year=2008, month=1, day=1),
                                datetime(year=2008, month=2, day=5))


def test_model_init():
    with pytest.raises(AssertionError):
        Model(1, Source.all, Past.all, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, 1, Past.all, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, 1, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, Past.all, 1)


header = '''format:
<ClSz>\t<TotFq>\t<Root>\t<ClusterId>
\t<QtFq>\t<Urls>\t<QtStr>\t<QuteId>
\t\t<Tm>\t<Fq>\t<UrlTy>\t<Url>

'''


empty_source = '''
2\t1\toh yes it's real that i love pooda\t1
\t0\t0\toh yes it's real that i love pooda\t1

\t1\t1\tit's real that i love bladi\t2
\t\t2008-08-01 00:00:00\t1\tB\tsome-url
'''


source_at_durl = '''
2\t2\toh yes it's real that i love pooda\t1
\t1\t1\toh yes it's real that i love pooda\t1
\t\t2008-08-01 00:00:00\t1\tB\tsome-url

\t1\t1\tit's real that i love bladi\t2
\t\t2008-08-01 00:00:00\t1\tB\tsome-url
'''


raw_cluster = '''
2\t3\toh yes it's real that i love pooda\t1
\t2\t2\toh yes it's real that i love pooda\t1
\t\t{source1}\t1\tM\tsome-url
\t\t{source2}\t1\tB\tsome-url

\t1\t1\tit's real that i love bladi\t2
\t\t{dest}\t1\tB\tsome-url
'''


raw_cluster2 = '''
3\t4\toh yes it's real that i love pooda\t1
\t2\t2\toh yes it's real that i love pooda\t1
\t\t{source1}\t1\tM\tsome-url
\t\t{source2}\t1\tB\tsome-url

\t1\t1\tit's real that i love bladi\t2
\t\t{dest}\t1\tB\tsome-url

\t1\t1\tit's real that i love bladi\t3
\t\t{other}\t1\tB\tsome-url
'''

raw_cluster3 = '''
3\t5\toh yes it's real that i love pooda\t1
\t2\t2\toh yes it's real that i love pooda\t1
\t\t{source1}\t1\tM\tsome-url
\t\t{source2}\t1\tB\tsome-url

\t1\t1\tit's real that i love bladi\t2
\t\t{dest}\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t3
\t\t{other1}\t1\tB\tsome-url
\t\t{other2}\t1\tB\tsome-url
'''


raw_cluster4 = '''
2\t3\toh yes it's real that i love pooda\t1
\t1\t1\toh yes it's real that i love pooda\t1
\t\t{source}\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t2
\t\t{dest}\t1\tB\tsome-url
\t\t{dest_other}\t1\tB\tsome-url
'''


raw_cluster5 = '''
2\t4\toh yes it's real that i love pooda\t1
\t1\t1\toh yes it's real that i love pooda\t1
\t\t{source}\t1\tB\tsome-url

\t3\t3\tit's real that i love bladi\t2
\t\t{dest}\t1\tB\tsome-url
\t\t{dest_other1}\t1\tB\tsome-url
\t\t{dest_other2}\t1\tB\tsome-url
'''


validation_cases = {
    '_validate_base': {
        (Time.continuous, None, Past.all, None): {
            True: {
                'source in past':
                    raw_cluster.format(source1='2008-07-13 14:00:00',
                                       source2='2008-07-31 01:00:00',
                                       dest='2008-08-01 00:00:00')
            },
            False: {
                'empty source': empty_source,
                'source at durl': source_at_durl,
                'source after past':
                    raw_cluster.format(source1='2008-09-13 14:45:39',
                                       source2='2008-09-17 04:09:03',
                                       dest='2008-08-01 00:00:00')
            }
        },
        (Time.continuous, None, Past.last_bin, None): {
            True: {
                'source in past':
                    raw_cluster.format(source1='2008-07-13 14:00:00',
                                       source2='2008-07-31 01:00:00',
                                       dest='2008-08-01 00:00:00')
            },
            False: {
                'empty source': empty_source,
                'source at durl': source_at_durl,
                'source before past':
                    raw_cluster.format(source1='2008-07-31 01:00:00',
                                       source2='2008-07-01 14:45:39',
                                       dest='2008-08-01 02:00:00'),
                'source before and after past':
                    raw_cluster.format(source1='2008-07-31 01:00:00',
                                       source2='2008-08-01 14:45:39',
                                       dest='2008-08-01 02:00:00'),
                'source after past':
                    raw_cluster.format(source1='2008-09-13 14:45:39',
                                       source2='2008-09-17 04:09:03',
                                       dest='2008-08-01 00:00:00'),
            }
        },
        (Time.discrete, None, Past.all, None): {
            True: {
                'source in past':
                    raw_cluster.format(source1='2008-07-13 14:00:00',
                                       source2='2008-07-31 01:00:00',
                                       dest='2008-08-01 00:00:00')
            },
            False: {
                'empty source': empty_source,
                'source at durl': source_at_durl,
                'source after past (before durl, non-empty first bin)':
                    raw_cluster2.format(other='2008-07-01 00:00:00',
                                        source1='2008-08-01 01:00:00',
                                        source2='2008-08-01 01:30:00',
                                        dest='2008-08-01 02:00:00'),
                'source after past (before durl, empty first bin)':
                    raw_cluster.format(source1='2008-08-01 01:00:00',
                                       source2='2008-08-01 01:30:00',
                                       dest='2008-08-01 02:00:00'),
                'source after past':
                    raw_cluster.format(source1='2008-09-01 01:00:00',
                                       source2='2008-09-01 01:30:00',
                                       dest='2008-08-01 02:00:00'),
            }
        },
        (Time.discrete, None, Past.last_bin, None): {
            True: {
                'source in past':
                    raw_cluster.format(source1='2008-07-13 14:00:00',
                                       source2='2008-07-31 00:00:00',
                                       dest='2008-08-01 00:00:00')
            },
            False: {
                'empty source': empty_source,
                'source at durl': source_at_durl,
                'source before past':
                    raw_cluster.format(source1='2008-07-30 01:00:00',
                                       source2='2008-07-30 23:00:00',
                                       dest='2008-08-01 00:00:00'),
                'source before and after past':
                    raw_cluster.format(source1='2008-07-30 23:00:00',
                                       source2='2008-08-01 14:00:00',
                                       dest='2008-08-01 02:00:00'),
                'source before and after past (before durl)':
                    raw_cluster.format(source1='2008-07-30 23:00:00',
                                       source2='2008-08-01 01:30:00',
                                       dest='2008-08-01 02:00:00'),
                'source before and after past':
                    raw_cluster.format(source1='2008-07-30 23:00:00',
                                       source2='2008-08-02 01:30:00',
                                       dest='2008-08-01 02:00:00'),
                'source after past (before durl, non-empty first bin)':
                    raw_cluster2.format(other='2008-07-01 00:00:00',
                                        source1='2008-08-01 01:00:00',
                                        source2='2008-08-01 01:30:00',
                                        dest='2008-08-01 02:00:00'),
                'source after past (before durl, empty first bin)':
                    raw_cluster.format(source1='2008-08-01 01:00:00',
                                       source2='2008-08-01 01:30:00',
                                       dest='2008-08-01 02:00:00'),
                'source after past':
                    raw_cluster.format(source1='2008-09-01 01:00:00',
                                       source2='2008-09-01 01:30:00',
                                       dest='2008-08-01 02:00:00'),
            }
        }
    },
    '_validate_source': {
        (None, Source.all, None, None): {
            # No fails, Source.all validates everything.
            True: {
                'empty source': empty_source,
                'source at durl': source_at_durl,
                'source in past':
                    raw_cluster.format(source1='2008-07-13 14:00:00',
                                       source2='2008-07-31 01:00:00',
                                       dest='2008-08-01 00:00:00')
            },
            False: {}
        },
        (Time.continuous, Source.majority, Past.all, None): {
            True: {
                'source is majority in past':
                    raw_cluster3.format(other1='2008-07-30 00:00:00',
                                        other2='2008-08-02 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-07-31 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-07-31 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            },
            False: {
                'empty source': empty_source,
                'source at durl':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly after durl':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-08-02 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after durl':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after durl with single other':
                    raw_cluster2.format(other='2008-07-22 00:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            }
        },
        (Time.continuous, Source.majority, Past.last_bin, None): {
            True: {
                'source is majority in past':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-07-31 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is majority in past with two occurrences':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-31 03:00:00',
                                        source1='2008-07-31 02:00:00',
                                        source2='2008-07-31 04:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past':
                    raw_cluster3.format(other1='2008-07-31 03:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past and at durl':
                    raw_cluster3.format(other1='2008-07-30 05:00:00',
                                        other2='2008-07-31 06:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            },
            False: {
                'empty source': empty_source,
                'source at durl':
                    raw_cluster3.format(other1='2008-07-31 05:00:00',
                                        other2='2008-07-31 06:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all before past':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-07-29 02:00:00',
                                        source2='2008-07-31 01:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly before past':
                    raw_cluster3.format(other1='2008-07-31 04:00:00',
                                        other2='2008-07-31 05:00:00',
                                        source1='2008-07-29 02:00:00',
                                        source2='2008-07-31 03:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source before and after past':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-07-31 01:00:00',
                                        source2='2008-08-01 03:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly after past':
                    raw_cluster3.format(other1='2008-07-31 04:00:00',
                                        other2='2008-07-31 05:00:00',
                                        source1='2008-07-31 02:00:00',
                                        source2='2008-08-02 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past with single other':
                    raw_cluster2.format(other='2008-07-22 00:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            }
        },
        (Time.discrete, Source.majority, Past.all, None): {
            True: {
                'source is majority in past':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-07-31 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past':
                    raw_cluster3.format(other1='2008-07-31 03:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past and at durl':
                    raw_cluster2.format(other='2008-07-30 05:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            },
            False: {
                'empty source': empty_source,
                'source at durl':
                    raw_cluster3.format(other1='2008-07-31 05:00:00',
                                        other2='2008-07-31 06:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly after past (before durl)':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-08-01 01:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past (before durl) with single other':
                    raw_cluster2.format(other='2008-07-29 00:00:00',
                                        source1='2008-08-01 01:00:00',
                                        source2='2008-08-01 01:30:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly after durl':
                    raw_cluster3.format(other1='2008-07-31 04:00:00',
                                        other2='2008-07-31 05:00:00',
                                        source1='2008-07-31 02:00:00',
                                        source2='2008-08-02 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after durl with single other':
                    raw_cluster2.format(other='2008-07-31 04:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past with single other':
                    raw_cluster2.format(other='2008-07-22 00:00:00',
                                        source1='2008-08-02 02:00:00',
                                        source2='2008-08-03 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            }
        },
        (Time.discrete, Source.majority, Past.last_bin, None): {
            True: {
                'source is majority in past':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-30 00:00:00',
                                        source1='2008-07-20 02:00:00',
                                        source2='2008-07-31 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is majority in past with two occurrences':
                    raw_cluster3.format(other1='2008-07-29 00:00:00',
                                        other2='2008-07-31 03:00:00',
                                        source1='2008-07-31 02:00:00',
                                        source2='2008-07-31 04:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past':
                    raw_cluster3.format(other1='2008-07-31 03:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past with single occurrence':
                    raw_cluster3.format(other1='2008-07-31 03:00:00',
                                        other2='2008-07-20 00:00:00',
                                        source1='2008-07-31 05:00:00',
                                        source2='2008-08-01 01:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source is ex-aequo in past and at durl':
                    raw_cluster3.format(other1='2008-07-30 05:00:00',
                                        other2='2008-07-31 06:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
            },
            False: {
                'empty source': empty_source,
                'source at durl':
                    raw_cluster3.format(other1='2008-07-31 05:00:00',
                                        other2='2008-07-31 06:00:00',
                                        source1='2008-07-31 04:00:00',
                                        source2='2008-08-01 02:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all before past':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-07-29 02:00:00',
                                        source2='2008-07-30 23:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly before past':
                    raw_cluster3.format(other1='2008-07-31 04:00:00',
                                        other2='2008-07-31 05:00:00',
                                        source1='2008-07-29 02:00:00',
                                        source2='2008-07-31 03:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source before and after past (before durl)':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-07-30 23:00:00',
                                        source2='2008-08-01 01:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source before and after past (after durl)':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-07-30 23:00:00',
                                        source2='2008-08-01 03:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source before and after durl (after past)':
                    raw_cluster3.format(other1='2008-07-30 04:00:00',
                                        other2='2008-07-30 05:00:00',
                                        source1='2008-08-01 01:00:00',
                                        source2='2008-08-01 03:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source partly after past':
                    raw_cluster3.format(other1='2008-07-31 04:00:00',
                                        other2='2008-07-31 05:00:00',
                                        source1='2008-07-31 02:00:00',
                                        source2='2008-08-01 01:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after durl':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-30 04:00:00',
                                        source1='2008-08-01 03:00:00',
                                        source2='2008-08-01 04:00:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past':
                    raw_cluster3.format(other1='2008-07-22 00:00:00',
                                        other2='2008-07-31 04:00:00',
                                        source1='2008-08-02 01:00:00',
                                        source2='2008-08-03 01:30:00',
                                        dest='2008-08-01 02:00:00'),
                'source all after past with single other':
                    raw_cluster2.format(other='2008-07-22 00:00:00',
                                        source1='2008-08-02 01:00:00',
                                        source2='2008-08-03 01:30:00',
                                        dest='2008-08-01 02:00:00'),
            }
        }
    },
    '_validate_durl': {
        (None, None, None, Durl.all): {
            # No fails, Durl.all validates everything.
            True: {
                'durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-30 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                },
                'durl.quote after durl': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-02 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 0
                },
                'durl.quote after past before durl': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 00:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                }
            }
        },
        (Time.continuous, None, Past.all, Durl.exclude_past): {
            True: {
                'durl.quote after past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-02 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 0
                },
                'durl.quote at durl': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 0
                },
            },
            False: {
                'durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-30 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                }
            }
        },
        (Time.continuous, None, Past.last_bin, Durl.exclude_past): {
            True: {
                'durl.quote before past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-30 23:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                },
                'durl.quote before and after past': {
                    'content':
                        raw_cluster5.format(source='2008-07-29 00:00:00',
                                            dest_other1='2008-07-30 23:00:00',
                                            dest_other2='2008-08-01 01:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                },
                'durl.quote after past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 01:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 0
                },
                'durl.quote at durl': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 0
                }
            },
            False: {
                'durl.quote at start of past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-31 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                },
                'durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-31 05:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                }
            }
        },
        (Time.discrete, None, Past.all, Durl.exclude_past): {
            True: {
                'durl.quote after past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 01:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                },
                'durl.quote at end of past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 00:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                }
            },
            False: {
                'durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-20 00:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                }
            }
        },
        (Time.discrete, None, Past.last_bin, Durl.exclude_past): {
            True: {
                'durl.quote before past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-30 23:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                },
                'durl.quote before and after past': {
                    'content':
                        raw_cluster5.format(source='2008-07-29 00:00:00',
                                            dest_other1='2008-07-30 23:00:00',
                                            dest_other2='2008-08-01 01:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 2
                },
                'durl.quote after past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 01:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                },
                'durl.quote at end of past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-08-01 00:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                }
            },
            False: {
                'durl.quote at start of past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-31 00:00:00',
                                            dest='2008-08-01 00:00:00'),
                    'occurrence': 1
                },
                'durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-29 00:00:00',
                                            dest_other='2008-07-31 05:00:00',
                                            dest='2008-08-01 02:00:00'),
                    'occurrence': 1
                }
            }
        }
    },
    # Hand-picked tests for the combination of the three _validate_* methods
    'validate': {
        (Time.continuous, Source.majority, Past.last_bin, Durl.all): {
            True: {
                'all good':
                    raw_cluster3.format(source1='2008-07-31 05:00:00',
                                        source2='2008-08-01 02:00:00',
                                        other1='2008-07-30 00:00:00',
                                        other2='2008-07-31 06:00:00',
                                        dest='2008-08-01 03:00:00')
            },
            False: {
                'fail _validate_base: source not in past':
                    raw_cluster3.format(source1='2008-07-30 05:00:00',
                                        source2='2008-07-30 02:00:00',
                                        other1='2008-07-30 00:00:00',
                                        other2='2008-07-31 06:00:00',
                                        dest='2008-08-01 03:00:00')
            }
        },
        (Time.discrete, Source.majority, Past.last_bin, Durl.all): {
            False: {
                'fail _validate_source: source not majority in past':
                    raw_cluster3.format(source1='2008-07-31 05:00:00',
                                        source2='2008-07-30 02:00:00',
                                        other1='2008-07-31 06:00:00',
                                        other2='2008-07-31 07:00:00',
                                        dest='2008-08-01 03:00:00')
            }
        },
        (Time.discrete, Source.all, Past.last_bin, Durl.exclude_past): {
            False: {
                'fail _validate_durl: durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-31 05:00:00',
                                            dest_other='2008-07-31 07:00:00',
                                            dest='2008-08-01 03:00:00'),
                    'occurrence': 1
                }
            }
        }
    }
}


def load_db(content):
    fd, filepath = mkstemp()
    with open(fd, 'w') as tmp:
        tmp.write(content)

    line_count = content.count('\n') + 1
    MemeTrackerParser(filepath, line_count=line_count).parse()
    os.remove(filepath)


validation_params = [
    (validation_type, time, source, past, durl, success, string)
    for (validation_type, models) in validation_cases.items()
    for ((time, source, past, durl), successes) in models.items()
    for (success, strings) in successes.items()
    for string in strings.keys()
]


@pytest.fixture(params=validation_params,
                ids=['{}'.format(param) for param in validation_params])
def validation_db(request, tmpdb):
    validation_type, time, source, past, durl, success, string = request.param
    content = validation_cases[
        validation_type][(time, source, past, durl)][success][string]
    if isinstance(content, dict):
        # The test case specifies the occurrence of the destination quote to
        # use as durl
        occurrence = content['occurrence']
        content = content['content']
    else:
        # Otherwise, default to 0.
        occurrence = 0
    load_db(header + content)
    return (validation_type, time, source, past, durl, success, occurrence)


def test_model_validate(validation_db):
    (validation_type, time, source, past,
     durl, success, occurrence) = validation_db

    times = list(Time) if time is None else [time]
    sources = list(Source) if source is None else [source]
    past = list(Past) if past is None else [past]
    durl = list(Durl) if durl is None else [durl]

    models = []
    for (time, source, past, durl) in product(times, sources, past, durl):
        models.append(Model(time, source, past, durl))

    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        dest = session.query(Quote).filter_by(sid=2).one()
        for model in models:
            validator = getattr(model, validation_type)
            assert validator(source, dest.urls[occurrence]) == success


cases_past = {
    (Time.continuous, Past.all): {
        'normal past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=20, hour=1),
                         datetime(year=2008, month=8, day=1, hour=2))
        },
        'empty past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=2),
                         datetime(year=2008, month=7, day=15, hour=2))
        },
    },
    (Time.continuous, Past.last_bin): {
        'normal past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=31, hour=2),
                         datetime(year=2008, month=8, day=1, hour=2))
        },
        'empty past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=2),
                         datetime(year=2008, month=7, day=15, hour=2))
        },
        'start-truncated': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-20 03:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=20, hour=1),
                         datetime(year=2008, month=7, day=20, hour=3))
        },
    },
    (Time.discrete, Past.all): {
        'normal past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=20, hour=1),
                         datetime(year=2008, month=8, day=1, hour=0))
        },
        'empty past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=2),
                         datetime(year=2008, month=7, day=15, hour=2))
        },
        'empty past with url before durl': {
            'content':
                raw_cluster.format(source1='2008-07-15 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=1),
                         datetime(year=2008, month=7, day=15, hour=1))
        },
        'durl at bin seam': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 00:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=20, hour=1),
                         datetime(year=2008, month=8, day=1, hour=0))
        },
    },
    (Time.discrete, Past.last_bin): {
        'normal past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=31, hour=0),
                         datetime(year=2008, month=8, day=1, hour=0))
        },
        'empty past': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=2),
                         datetime(year=2008, month=7, day=15, hour=2))
        },
        'empty past with url before durl': {
            'content':
                raw_cluster.format(source1='2008-07-15 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-15 02:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=15, hour=1),
                         datetime(year=2008, month=7, day=15, hour=1))
        },
        'start-truncated': {
            'content':
                raw_cluster.format(source1='2008-07-19 04:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-07-20 03:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=19, hour=4),
                         datetime(year=2008, month=7, day=20, hour=0))
        },
        'durl at bin seam': {
            'content':
                raw_cluster.format(source1='2008-07-20 01:00:00',
                                   source2='2008-07-25 01:00:00',
                                   dest='2008-08-01 00:00:00'),
            'interval':
                Interval(datetime(year=2008, month=7, day=31, hour=0),
                         datetime(year=2008, month=8, day=1, hour=0))
        }
    }
}


past_params = [(time, past, string)
               for ((time, past), strings) in cases_past.items()
               for string in strings.keys()]


@pytest.fixture(params=past_params,
                ids=['{}'.format(param) for param in past_params])
def past_db(request, tmpdb):
    time, past, string = request.param
    content = cases_past[(time, past)][string]['content']
    interval = cases_past[(time, past)][string]['interval']
    load_db(header + content)
    return time, past, interval


def test_model_past(past_db):
    time, past, interval = past_db

    sources = list(Source)
    durl = list(Durl)

    models = []
    for (source, durl) in product(sources, durl):
        models.append(Model(time, source, past, durl))

    with session_scope() as session:
        destination = session.query(Quote).filter_by(sid=2).one()
        durl = destination.urls[0]
        cluster = durl.quote.cluster
        for model in models:
            assert model._past(cluster, durl) == interval
