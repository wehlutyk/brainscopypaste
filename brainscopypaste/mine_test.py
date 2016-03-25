import os
from tempfile import mkstemp
from datetime import datetime
from itertools import product

import pytest

from brainscopypaste.load import MemeTrackerParser
from brainscopypaste.mine import (Interval, Model, Time, Source, Past, Durl,
                                  ClusterMinerMixin,
                                  SubstitutionValidatorMixin,
                                  mine_substitutions_with_model)
from brainscopypaste.filter import filter_clusters
from brainscopypaste.db import Cluster, Quote, Substitution
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


def test_model_eq():
    assert Model(Time.continuous, Source.all, Past.all, Durl.all) == \
        Model(Time.continuous, Source.all, Past.all, Durl.all)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all) != \
        Model(Time.discrete, Source.all, Past.all, Durl.all)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all) != \
        Model(Time.continuous, Source.majority, Past.all, Durl.all)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all) != \
        Model(Time.continuous, Source.all, Past.last_bin, Durl.all)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all) != \
        Model(Time.continuous, Source.all, Past.all, Durl.exclude_past)


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

\t1\t1\tit's real that he loves bladi\t2
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


raw_cluster6 = '''
1\t5\toh yes it's real that i love pooda\t1
\t5\t5\toh yes it's real that i love pooda\t1
\t\t{source1}\t1\tB\tsome-url-1
\t\t{source2}\t1\tB\tsome-url-2
\t\t{source3}\t1\tB\tsome-url-3
\t\t{source4}\t1\tB\tsome-url-4
\t\t{source5}\t1\tB\tsome-url-5
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


past_cases = {
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
               for ((time, past), strings) in past_cases.items()
               for string in strings.keys()]


@pytest.fixture(params=past_params,
                ids=['{}'.format(param) for param in past_params])
def past_db(request, tmpdb):
    time, past, string = request.param
    content = past_cases[(time, past)][string]['content']
    interval = past_cases[(time, past)][string]['interval']
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


past_surls_cases = {
    (Time.continuous, Past.all): {
        'content':
            raw_cluster6.format(source5='2008-07-20 02:00:00',
                                source2='2008-07-31 02:00:00',
                                source3='2008-08-01 01:00:00',
                                source4='2008-08-01 02:00:00',
                                source1='2008-08-03 06:00:00'),
        'occurrence': 3,
        'past_surls': [5, 2, 3]
    },
    (Time.continuous, Past.last_bin): {
        'content':
            raw_cluster6.format(source5='2008-07-20 02:00:00',
                                source2='2008-07-31 02:00:00',
                                source3='2008-08-01 01:00:00',
                                source4='2008-08-01 02:00:00',
                                source1='2008-08-03 06:00:00'),
        'occurrence': 3,
        'past_surls': [2, 3]
    },
    (Time.discrete, Past.all): {
        'content':
            raw_cluster6.format(source5='2008-07-20 02:00:00',
                                source2='2008-07-31 02:00:00',
                                source3='2008-08-01 01:00:00',
                                source4='2008-08-01 02:00:00',
                                source1='2008-08-03 06:00:00'),
        'occurrence': 3,
        'past_surls': [5, 2]
    },
    (Time.discrete, Past.last_bin): {
        'content':
            raw_cluster6.format(source5='2008-07-20 02:00:00',
                                source2='2008-07-31 02:00:00',
                                source3='2008-08-01 01:00:00',
                                source4='2008-08-01 02:00:00',
                                source1='2008-08-03 06:00:00'),
        'occurrence': 3,
        'past_surls': [2]
    }
}


@pytest.fixture(params=past_surls_cases.keys(),
                ids=['{}'.format(param) for param in past_surls_cases.keys()])
def past_surls_db(request, tmpdb):
    time, past = request.param
    content = past_surls_cases[(time, past)]['content']
    occurrence = past_surls_cases[(time, past)]['occurrence']
    expected_surl_ids = past_surls_cases[(time, past)]['past_surls']
    load_db(header + content)
    return time, past, occurrence, expected_surl_ids


def test_model_past_surls(past_surls_db):
    time, past, occurrence, expected_surl_ids = past_surls_db

    sources = list(Source)
    durl = list(Durl)

    models = []
    for (source, durl) in product(sources, durl):
        models.append(Model(time, source, past, durl))

    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        cluster = source.cluster
        durl = source.urls[occurrence]
        for model in models:
            past_surl_ids = [int(url.url[-1])
                             for url in model.past_surls(cluster, durl)]
            assert past_surl_ids == expected_surl_ids


def test_cluster_miner_mixin_substitution_ok(tmpdb):
    # Set up database
    load_db(header + raw_cluster5.format(source='2008-07-31 05:00:00',
                                         dest_other1='2008-07-31 06:00:00',
                                         dest='2008-08-01 06:00:00',
                                         dest_other2='2008-08-02 02:00:00'))

    # Test
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all)
    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        durl = session.query(Quote).filter_by(sid=2).one().urls[1]
        substitution = ClusterMinerMixin._substitution(source, durl, 2, model)
        assert substitution.occurrence == 1
        assert substitution.start == 2
        assert substitution.position == 6
        assert substitution.source.sid == 1
        assert substitution.destination.sid == 2
        assert substitution.model == model
        assert substitution.tags == ('NN', 'NNS')
        assert substitution.tokens == ('pooda', 'bladi')
        assert substitution.lemmas == ('pooda', 'bladi')


def test_cluster_miner_mixin_substitution_too_many_changes(tmpdb):
    # Set up database
    load_db(header + raw_cluster.format(source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 06:00:00'))

    # Test
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all)
    with pytest.raises(AssertionError):
        with session_scope() as session:
            source = session.query(Quote).filter_by(sid=1).one()
            durl = session.query(Quote).filter_by(sid=2).one().urls[0]
            ClusterMinerMixin._substitution(source, durl, 2, model)


def test_substitution_validator_mixin():
    svm = SubstitutionValidatorMixin()
    cases = {
        False: [{
            # Stopwords
            'tokens': ('yes', 'no'),
            'lemmas': ('lemmaaa', 'lemmmoooo')
        }, {
            # Stopwords
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('i', 'do')
        }, {
            # Identical words
            'tokens': ('word', 'word'),
            'lemmas': ('lemmaaa', 'lemmmoooo')
        }, {
            # Identical lemmas
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('lemma', 'lemma')
        }, {
            # Abbreviation
            'tokens': ('senator', 'sen'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # Abbreviation
            'tokens': ('flu', 'fluviator'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # Abbreviation
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('blooom', 'blo')
        }, {
            # Shortening
            'tokens': ('programme', 'program'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # Shortening
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('goddam', 'goddamme'),
        }, {
            # US/UK spelling
            'tokens': ('blodder', 'bloddre'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # US/UK spelling
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('bildre', 'bilder')
        }, {
            # Numbers
            'tokens': ('1st', '2nd'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # Numbers
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('3rd', 'fourth')
        }, {
            # Minor spelling changes
            'tokens': ('plural', 'plurals'),
            'lemmas': ('lemmaaa', 'lemmoooo')
        }, {
            # Minor spelling changes
            'tokens': ('wordi', 'wordooo'),
            'lemmas': ('neighbour', 'neighbor')
        }],
        True: [{
            'tokens': ('hello', 'tchuss'),
            'lemmas': ('hello', 'tchuss')
        }, {
            'tokens': ('tree', 'band'),
            'lemmas': ('tree', 'willness')
        }]
    }

    for success, token_lemma_list in cases.items():
        for tokens_lemmas in token_lemma_list:
            svm.tokens = tokens_lemmas['tokens']
            svm.lemmas = tokens_lemmas['lemmas']
            print(svm.tokens, svm.lemmas)
            print(success)
            assert svm.validate() == success


substitutions_cases = {
    # Time.discrete, some basic checks
    (Time.discrete, Source.all, Past.last_bin, Durl.all): {
        'no substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest='2008-07-30 02:00:00',
                                           dest_other1='2008-07-31 03:00:00',
                                           dest_other2='2008-08-02 05:00:00'),
            'substitutions': []
        },
        'one substitution': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest='2008-07-30 02:00:00',
                                           dest_other1='2008-08-01 03:00:00',
                                           dest_other2='2008-08-02 05:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1}
            ]
        },
        'two substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest='2008-07-30 02:00:00',
                                           dest_other1='2008-08-01 00:00:00',
                                           dest_other2='2008-08-01 05:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 2}
            ]
        },
        'three substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 00:00:00',
                                           dest='2008-08-01 02:00:00',
                                           dest_other1='2008-08-01 06:00:00',
                                           dest_other2='2008-08-01 22:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 2}
            ]
        }
    },
    # Time.continuous, majority effects
    (Time.continuous, Source.majority, Past.last_bin, Durl.all): {
        'alternation': {
            'content': '''
2\t7\tit's real that i love pooda\t1
\t4\t3\tit's real that i love pooda\t1
\t\t2008-07-31 00:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t2\tB\tsome-url

\t3\t2\tit's real that i love bladi\t2
\t\t2008-07-31 08:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t2\tB\tsome-url
''',
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
                {'source_sid': 2, 'destination_sid': 1, 'occurrence': 1},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
                {'source_sid': 2, 'destination_sid': 1, 'occurrence': 2},
            ]
        },
        'majority change': {
            'content': '''
2\t6\tit's real that i love pooda\t1
\t4\t4\tit's real that i love pooda\t1
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t2
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t1\tB\tsome-url
''',
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
                {'source_sid': 2, 'destination_sid': 1, 'occurrence': 1},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
            ]
        },
        'majority change with competition': {
            'content': '''
3\t10\tit's real that i love pooda\t1
\t4\t4\tit's real that i love pooda\t1
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t2
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t1\tB\tsome-url

\t4\t4\tsome other irrelevant but majority quote\t3
\t\t2008-07-31 11:00:00\t1\tB\tsome-url
\t\t2008-07-31 15:00:00\t1\tB\tsome-url
\t\t2008-07-31 22:00:00\t1\tB\tsome-url
\t\t2008-07-31 23:00:00\t1\tB\tsome-url
''',
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
            ]
        }
    },
    # Time.continuous past exclusion (from last_bin)
    (Time.continuous, Source.all, Past.last_bin, Durl.exclude_past): {
        'one substitution': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest_other1='2008-07-30 23:00:00',
                                           dest='2008-08-01 00:00:00',
                                           dest_other2='2008-08-01 01:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
            ]
        },
    },
    # Time.continuous past exclusion (from all)
    (Time.continuous, Source.all, Past.all, Durl.exclude_past): {
        'no substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest_other1='2008-07-30 23:00:00',
                                           dest='2008-08-01 00:00:00',
                                           dest_other2='2008-08-01 01:00:00'),
            'substitutions': []
        },
        'one substitution': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest='2008-08-01 00:00:00',
                                           dest_other1='2008-08-01 00:30:00',
                                           dest_other2='2008-08-01 01:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
            ]
        },
    },
    # Time.discrete majority effect and past exclusion
    (Time.discrete, Source.majority, Past.last_bin, Durl.exclude_past): {
        'majority change and past exclusion': {
            'content': '''
2\t7\tit's real that i love pooda\t1
\t5\t5\tit's real that i love pooda\t1
\t\t2008-07-31 05:00:00\t1\tM\tsome-url
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-07-31 12:00:00\t1\tB\tsome-url
\t\t2008-08-01 05:00:00\t1\tB\tsome-url
\t\t2008-08-02 05:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t2
\t\t2008-08-01 06:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url
''',
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
                {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
            ]
        }
    }
}


substitutions_params = [
    (time, source, past, durl, string)
    for (time, source, past, durl), model_cases in substitutions_cases.items()
    for string in model_cases.keys()
]


@pytest.fixture(params=substitutions_params,
                ids=['{}'.format(param) for param in substitutions_params])
def substitutions_db(request, tmpdb):
    time, source, past, durl, string = request.param
    content = substitutions_cases[
        (time, source, past, durl)][string]['content']
    expected_substitutions = substitutions_cases[
        (time, source, past, durl)][string]['substitutions']
    load_db(header + content)
    return Model(time, source, past, durl), expected_substitutions


def test_cluster_miner_mixin_substitutions(substitutions_db):
    model, expected_substitutions = substitutions_db

    with session_scope() as session:
        cluster = session.query(Cluster).filter_by(sid=1).one()
        substitutions = sorted((s.source.sid, s.destination.sid, s.occurrence)
                               for s in cluster.substitutions(model))
        assert substitutions == sorted((s['source_sid'],
                                        s['destination_sid'],
                                        s['occurrence'])
                                       for s in expected_substitutions)


mine_substitutions_content = (
    '''
3\t8\tit's real that i love pooda\t1'''
    # The first part of this cluster defines basic substitutions.
    '''
\t4\t3\tit's real that i love pooda\t1
\t\t2008-07-31 00:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t2\tB\tsome-url

\t3\t2\tit's real that i love bladi\t2
\t\t2008-07-31 08:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t2\tB\tsome-url
'''
    # This substitution here will not validate() ('poo' abbreviates 'pooda'),
    # and we're making sure the non-validation doesn't wipe out the previously
    # detected substitutions.
    '''
\t1\t1\tit's real that i love poo\t3
\t\t2008-08-02 07:00:00\t1\tB\tsome-url
'''
    # Change of majority quote.
    '''
2\t6\tit's real that i love pooda\t2
\t4\t4\tit's real that i love pooda\t4
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t5
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t1\tB\tsome-url
'''
    # Majority masquing.
    '''
3\t10\tit's real that i love pooda\t3
\t4\t4\tit's real that i love pooda\t6
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love bladi\t7
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t1\tB\tsome-url

\t4\t4\tsome other irrelevant but majority quote\t8
\t\t2008-07-31 11:00:00\t1\tB\tsome-url
\t\t2008-07-31 15:00:00\t1\tB\tsome-url
\t\t2008-07-31 22:00:00\t1\tB\tsome-url
\t\t2008-07-31 23:00:00\t1\tB\tsome-url
'''
    # Cluster filtered out.
    '''
3\t3\tsome cluster that will get filtered out\t4
\t1\t1\tsome group that will get filtered out\t9
\t\t2008-02-01 00:00:00\t1\tM\tsome-url

\t1\t1\tsome cluster that will get filtered out\t10
\t\t2008-07-31 10:00:00\t1\tB\tsome-url

\t1\t1\tsome cluster that will get wiped out\t11
\t\t2008-08-01 02:00:00\t1\tB\tsome-url
''')


mine_substitutions_cases = {
    'full mining': {
        'limit': None,
        'substitutions': [
            # Cluster 1.
            {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
            {'source_sid': 2, 'destination_sid': 1, 'occurrence': 1},
            {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
            {'source_sid': 2, 'destination_sid': 1, 'occurrence': 2},
            # Cluster 2.
            {'source_sid': 4, 'destination_sid': 5, 'occurrence': 0},
            {'source_sid': 5, 'destination_sid': 4, 'occurrence': 1},
            {'source_sid': 4, 'destination_sid': 5, 'occurrence': 1},
            # Cluster 3.
            {'source_sid': 6, 'destination_sid': 7, 'occurrence': 0}
            # Cluster 4: nothing (filtered out).
        ]
    },
    'with limit': {
        'limit': 1,
        'substitutions': [
            # Cluster 1.
            {'source_sid': 1, 'destination_sid': 2, 'occurrence': 0},
            {'source_sid': 2, 'destination_sid': 1, 'occurrence': 1},
            {'source_sid': 1, 'destination_sid': 2, 'occurrence': 1},
            {'source_sid': 2, 'destination_sid': 1, 'occurrence': 2},
            # Clusters 2, 3, 4: nothing (because of the limit).
        ]
    }
}


@pytest.fixture(params=mine_substitutions_cases.keys(),
                ids=['{}'.format(param)
                     for param in mine_substitutions_cases.keys()])
def mine_substitutions_db(request, tmpdb):
    string = request.param
    limit = mine_substitutions_cases[string]['limit']
    expected_substitutions = mine_substitutions_cases[string]['substitutions']
    load_db(header + mine_substitutions_content)
    filter_clusters()
    return limit, expected_substitutions


def test_mine_substitutions_with_model(mine_substitutions_db):
    limit, expected_substitutions = mine_substitutions_db

    # Mine.
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all)
    mine_substitutions_with_model(model, limit=limit)

    # Test.
    with session_scope() as session:
        substitutions = sorted((s.source.sid, s.destination.sid, s.occurrence)
                               for s in session.query(Substitution))
        assert substitutions == sorted((s['source_sid'],
                                        s['destination_sid'],
                                        s['occurrence'])
                                       for s in expected_substitutions)

    # Check we can't mine again.
    with pytest.raises(Exception) as excinfo:
        mine_substitutions_with_model(model, limit=limit)
    assert 'already some mined substitutions' in str(excinfo.value)
