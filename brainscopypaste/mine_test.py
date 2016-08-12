"""Tests for :mod:`.mine`.

"""


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
from brainscopypaste.utils import session_scope, Namespace
from brainscopypaste.conf import settings


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
        Model(1, Source.all, Past.all, Durl.all, 1)
    with pytest.raises(AssertionError):
        Model(Time.continuous, 1, Past.all, Durl.all, 1)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, 1, Durl.all, 1)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, Past.all, 1, 1)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, Past.all, Durl.all, 0)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, Past.all, Durl.all,
              settings.MT_FILTER_MIN_TOKENS)
    assert Model(Time.continuous, Source.all,
                 Past.all, Durl.all, 2) is not None


def test_model_eq():
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) == \
        Model(Time.continuous, Source.all, Past.all, Durl.all, 1)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 2) == \
        Model(Time.continuous, Source.all, Past.all, Durl.all, 2)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) != \
        Model(Time.discrete, Source.all, Past.all, Durl.all, 1)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) != \
        Model(Time.continuous, Source.majority, Past.all, Durl.all, 1)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) != \
        Model(Time.continuous, Source.all, Past.last_bin, Durl.all, 1)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) != \
        Model(Time.continuous, Source.all, Past.all, Durl.exclude_past, 1)
    assert Model(Time.continuous, Source.all, Past.all, Durl.all, 1) != \
        Model(Time.continuous, Source.all, Past.all, Durl.all, 2)


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

raw_cluster7 = '''
2\t2\toh yes it's real that i love pooda\t1
\t1\t1\t{source_string}\t1
\t\t{source}\t1\tM\tsome-url

\t1\t1\t{dest_string}\t2
\t\t{dest}\t1\tB\tsome-url
'''


validation_cases = {
    '_validate_base': {
        (Time.continuous, None, Past.all, None, None): {
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
        (Time.continuous, None, Past.last_bin, None, None): {
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
        (Time.discrete, None, Past.all, None, None): {
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
        (Time.discrete, None, Past.last_bin, None, None): {
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
        (None, Source.all, None, None, None): {
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
        (Time.continuous, Source.majority, Past.all, None, None): {
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
        (Time.continuous, Source.majority, Past.last_bin, None, None): {
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
        (Time.discrete, Source.majority, Past.all, None, None): {
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
        (Time.discrete, Source.majority, Past.last_bin, None, None): {
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
        (None, None, None, Durl.all, None): {
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
        (Time.continuous, None, Past.all, Durl.exclude_past, None): {
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
        (Time.continuous, None, Past.last_bin, Durl.exclude_past, None): {
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
        (Time.discrete, None, Past.all, Durl.exclude_past, None): {
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
        (Time.discrete, None, Past.last_bin, Durl.exclude_past, None): {
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
    '_validate_distance': {
        (None, None, None, None, 1): {
            True: {
                'one substitution': raw_cluster7.format(
                    source='2008-07-30 12:00:00',
                    source_string="she walked around the cat",
                    dest='2008-07-31 06:00:00',
                    dest_string="she walked around the dog"
                ),
            },
            False: {
                'two substitutions': raw_cluster7.format(
                    source='2008-07-30 12:00:00',
                    source_string="she walked around the cat's fur",
                    dest='2008-07-31 06:00:00',
                    dest_string="she walked around the dog's tail"
                ),
            }
        },
        (None, None, None, None, 2): {
            True: {
                'one substitution': raw_cluster7.format(
                    source='2008-07-30 12:00:00',
                    source_string="she walked around the cat",
                    dest='2008-07-31 06:00:00',
                    dest_string="she walked around the dog"
                ),
                'two substitutions': raw_cluster7.format(
                    source='2008-07-30 12:00:00',
                    source_string="she walked around the cat's fur",
                    dest='2008-07-31 06:00:00',
                    dest_string="she walked around the dog's tail"
                ),
            },
            False: {
                'three substitutions': raw_cluster7.format(
                    source='2008-07-30 12:00:00',
                    source_string="she jumped around the cat's fur",
                    dest='2008-07-31 06:00:00',
                    dest_string="she walked around the dog's tail"
                ),
            }
        },
    },
    # Hand-picked tests for the combination of the three _validate_* methods
    'validate': {
        (Time.continuous, Source.majority, Past.last_bin, Durl.all, 1): {
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
        (Time.discrete, Source.majority, Past.last_bin, Durl.all, 1): {
            False: {
                'fail _validate_source: source not majority in past':
                    raw_cluster3.format(source1='2008-07-31 05:00:00',
                                        source2='2008-07-30 02:00:00',
                                        other1='2008-07-31 06:00:00',
                                        other2='2008-07-31 07:00:00',
                                        dest='2008-08-01 03:00:00')
            }
        },
        (Time.discrete, Source.all, Past.last_bin, Durl.exclude_past, 1): {
            False: {
                'fail _validate_durl: durl.quote in past': {
                    'content':
                        raw_cluster4.format(source='2008-07-31 05:00:00',
                                            dest_other='2008-07-31 07:00:00',
                                            dest='2008-08-01 03:00:00'),
                    'occurrence': 1
                }
            }
        },
        (Time.discrete, Source.all, Past.last_bin, Durl.exclude_past, 1): {
            True: {
                'all good':
                    raw_cluster7.format(
                        source='2008-07-30 12:00:00',
                        source_string="she walked around the cat",
                        dest='2008-07-31 06:00:00',
                        dest_string="she walked around the dog"
                    )
            },
            False: {
                'fail _validate_distance: too many substitutions':
                    raw_cluster7.format(
                        source='2008-07-30 12:00:00',
                        source_string="she walked around the cat's fur",
                        dest='2008-07-31 06:00:00',
                        dest_string="she walked around the dog's tail"
                    )
            }
        },
        (Time.discrete, Source.all, Past.last_bin, Durl.exclude_past, 2): {
            True: {
                'all good':
                    raw_cluster7.format(
                        source='2008-07-30 12:00:00',
                        source_string="she walked around the cat's fur",
                        dest='2008-07-31 06:00:00',
                        dest_string="she walked around the dog's tail"
                    )
            },
            False: {
                'fail _validate_distance: too many substitutions':
                    raw_cluster7.format(
                        source='2008-07-30 12:00:00',
                        source_string="she walked around the cat's fur",
                        dest='2008-07-31 06:00:00',
                        dest_string="she jumped around the dog's tail"
                    )
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
    (validation_type, time, source, past, durl, max_distance, success, string)
    for (validation_type, models) in validation_cases.items()
    for ((time, source, past, durl, max_distance), successes) in models.items()
    for (success, strings) in successes.items()
    for string in strings.keys()
]


@pytest.fixture(params=validation_params,
                ids=['{}'.format(param) for param in validation_params])
def validation_db(request, tmpdb):
    (validation_type, time, source, past, durl, max_distance,
     success, string) = request.param
    content = validation_cases[
        validation_type][(time, source, past, durl, max_distance)][
        success][string]
    if isinstance(content, dict):
        # The test case specifies the occurrence of the destination quote to
        # use as durl
        occurrence = content['occurrence']
        content = content['content']
    else:
        # Otherwise, default to 0.
        occurrence = 0
    load_db(header + content)
    return (validation_type, time, source, past, durl, max_distance,
            success, occurrence)


def test_model_validate(validation_db):
    (validation_type, time, source, past, durl, max_distance,
     success, occurrence) = validation_db

    times = list(Time) if time is None else [time]
    sources = list(Source) if source is None else [source]
    pasts = list(Past) if past is None else [past]
    durls = list(Durl) if durl is None else [durl]
    max_distances = (range(1, 1 + settings.MT_FILTER_MIN_TOKENS // 2)
                     if max_distance is None else [max_distance])

    models = []
    for (time, source, past, durl, max_distance) in product(
            times, sources, pasts, durls, max_distances):
        models.append(Model(time, source, past, durl, max_distance))

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
    durls = list(Durl)
    max_distances = range(1, 1 + settings.MT_FILTER_MIN_TOKENS // 2)

    models = []
    for (source, durl, max_distance) in product(sources, durls, max_distances):
        models.append(Model(time, source, past, durl, max_distance))

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
    durls = list(Durl)
    max_distances = range(1, 1 + settings.MT_FILTER_MIN_TOKENS // 2)

    models = []
    for (source, durl, max_distance) in product(sources, durls, max_distances):
        models.append(Model(time, source, past, durl, max_distance))

    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        cluster = source.cluster
        durl = source.urls[occurrence]
        for model in models:
            past_surl_ids = [int(url.url[-1])
                             for url in model.past_surls(cluster, durl)]
            assert past_surl_ids == expected_surl_ids


def test_cluster_miner_mixin_substitution_ok_one(tmpdb):
    # Set up database
    load_db(header + raw_cluster5.format(source='2008-07-31 05:00:00',
                                         dest_other1='2008-07-31 06:00:00',
                                         dest='2008-08-01 06:00:00',
                                         dest_other2='2008-08-02 02:00:00'))

    # Test
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all, 1)
    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        durl = session.query(Quote).filter_by(sid=2).one().urls[1]

        substitutions = list(ClusterMinerMixin._substitutions(source, durl,
                                                              model))
        assert len(substitutions) == 1

        substitution = substitutions[0]
        assert substitution.occurrence == 1
        assert substitution.start == 2
        assert substitution.position == 6
        assert substitution.source.sid == 1
        assert substitution.destination.sid == 2
        assert substitution.model == model
        assert substitution.tags == ('NN', 'NNS')
        assert substitution.tokens == ('pooda', 'bladi')
        assert substitution.lemmas == ('pooda', 'bladi')


def test_cluster_miner_mixin_substitution_ok_two(tmpdb):
    # Set up database
    load_db(header + raw_cluster.format(source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 06:00:00'))

    # Test
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all, 2)
    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        durl = session.query(Quote).filter_by(sid=2).one().urls[0]

        substitutions = list(ClusterMinerMixin._substitutions(source, durl,
                                                              model))
        assert len(substitutions) == 2

        s1 = substitutions[0]
        assert s1.occurrence == 0
        assert s1.start == 2
        assert s1.position == 4
        assert s1.source.sid == 1
        assert s1.destination.sid == 2
        assert s1.model == model
        assert s1.tags == ('NP', 'PP')
        assert s1.tokens == ('i', 'he')
        assert s1.lemmas == ('i', 'he')

        s2 = substitutions[1]
        assert s2.occurrence == 0
        assert s2.start == 2
        assert s2.position == 6
        assert s2.source.sid == 1
        assert s2.destination.sid == 2
        assert s2.model == model
        assert s2.tags == ('NN', 'NN')
        assert s2.tokens == ('pooda', 'bladi')
        assert s2.lemmas == ('pooda', 'bladi')


def test_cluster_miner_mixin_substitution_too_many_changes(tmpdb):
    # Set up database
    load_db(header + raw_cluster.format(source1='2008-07-31 05:00:00',
                                        source2='2008-07-31 06:00:00',
                                        dest='2008-08-01 06:00:00'))

    # Test
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all, 1)
    with pytest.raises(AssertionError):
        with session_scope() as session:
            source = session.query(Quote).filter_by(sid=1).one()
            durl = session.query(Quote).filter_by(sid=2).one().urls[0]
            for substitution in ClusterMinerMixin._substitutions(source, durl,
                                                                 model):
                pass


validator_mixin_cases = {
    False: {
        'only real-word lemmas': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('lemmaaa', 'lemmooo'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'stopwords (tokens)': {
            'tokens': ('yes', 'no'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'stopwords (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('i', 'do'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'identical words (tokens)': {
            'tokens': ('word', 'word'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'identical words (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('lemma', 'lemma'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'abbreviation (real)': {
            'tokens': ('senator', 'sen'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'abbreviation (non-word)': {
            'tokens': ('flu', 'fluviator'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'abbreviation (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('blooom', 'blo'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'shortening (tokens)': {
            'tokens': ('programme', 'program'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'shortening (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('goddam', 'goddamme'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'us/uk spelling (tokens)': {
            'tokens': ('blodder', 'bloddre'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'us/uk spelling (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('bildre', 'bilder'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'numbers (tokens)': {
            'tokens': ('1st', '2nd'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'numbers (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('3rd', 'fourth'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'minor spelling changes (tokens)': {
            'tokens': ('plural', 'plurals'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'minor spelling changes (lemmas)': {
            'tokens': ('tree', 'bush'),
            'lemmas': ('neighbour', 'neighbor'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'word deletion (right, 1st substitution)': {
            'tokens': ('highest', 'school'),
            'lemmas': ('high', 'school'),
            'source': {
                'tokens': ['this', 'is', 'highest', 'school'],
                'lemmas': ['this', 'be', 'high', 'school']
            },
            'destination': {
                'tokens': ['this', 'is', 'school', 'boy'],
                'lemmas': ['this', 'be', 'school', 'boy']
            },
            'position': 2,
            'start': 0
        },
        'word deletion (right, 2nd substitution)': {
            'tokens': ('school', 'boy'),
            'lemmas': ('school', 'boy'),
            'source': {
                'tokens': ['this', 'is', 'highest', 'school'],
                'lemmas': ['this', 'be', 'high', 'school']
            },
            'destination': {
                'tokens': ['this', 'is', 'school', 'boy'],
                'lemmas': ['this', 'be', 'school', 'boy']
            },
            'position': 3,
            'start': 0
        },
        'word deletion (left, 1st substitution)': {
            'tokens': ('highest', 'huge'),
            'lemmas': ('high', 'huge'),
            'source': {
                'tokens': ['huge', 'highest', 'school', 'is', 'the', 'best',
                           'thing'],
                'lemmas': ['huge', 'high', 'school', 'be', 'the', 'best',
                           'thing']
            },
            'destination': {
                'tokens': ['huge', 'highest', 'is', 'the', 'best', 'thing'],
                'lemmas': ['huge', 'high', 'be', 'the', 'best', 'thing']
            },
            'position': 0,
            'start': 1
        },
        'word deletion (left, 2nd substitution)': {
            'tokens': ('school', 'highest'),
            'lemmas': ('school', 'high'),
            'source': {
                'tokens': ['huge', 'highest', 'school', 'is', 'the', 'best',
                           'thing'],
                'lemmas': ['huge', 'high', 'school', 'be', 'the', 'best',
                           'thing']
            },
            'destination': {
                'tokens': ['huge', 'highest', 'is', 'the', 'best', 'thing'],
                'lemmas': ['huge', 'high', 'be', 'the', 'best', 'thing']
            },
            'position': 1,
            'start': 1
        },
        'two words deletion (right, 1st substitution)': {
            'tokens': ('of', 'is'),
            'lemmas': ('of', 'is'),
            'source': {
                'tokens': ['here', 'our', 'supply', 'of', 'energy', 'is',
                           'gone'],
                'lemmas': ['here', 'our', 'supply', 'of', 'energy', 'is', 'go']
            },
            'destination': {
                'tokens': ['our', 'supply', 'is', 'gone'],
                'lemmas': ['our', 'supply', 'is', 'go']
            },
            'position': 2,
            'start': 1
        },
        'two words deletion (right, 2nd substitution)': {
            'tokens': ('energy', 'gone'),
            'lemmas': ('energy', 'go'),
            'source': {
                'tokens': ['here', 'our', 'supply', 'of', 'energy', 'is',
                           'gone'],
                'lemmas': ['here', 'our', 'supply', 'of', 'energy', 'is', 'go']
            },
            'destination': {
                'tokens': ['our', 'supply', 'is', 'gone'],
                'lemmas': ['our', 'supply', 'is', 'go']
            },
            'position': 3,
            'start': 1
        },
        'two words deletion (left, 1st substitution)': {
            'tokens': ('of', 'our'),
            'lemmas': ('of', 'our'),
            'source': {
                'tokens': ['here', 'our', 'supply', 'of', 'energy', 'is',
                           'gone'],
                'lemmas': ['here', 'our', 'supply', 'of', 'energy', 'is', 'go']
            },
            'destination': {
                'tokens': ['our', 'supply', 'is', 'gone'],
                'lemmas': ['our', 'supply', 'is', 'go']
            },
            'position': 0,
            'start': 3
        },
        'two words deletion (left, 2nd substitution)': {
            'tokens': ('energy', 'supply'),
            'lemmas': ('energy', 'supply'),
            'source': {
                'tokens': ['here', 'our', 'supply', 'of', 'energy', 'is',
                           'gone'],
                'lemmas': ['here', 'our', 'supply', 'of', 'energy', 'is', 'go']
            },
            'destination': {
                'tokens': ['our', 'supply', 'is', 'gone'],
                'lemmas': ['our', 'supply', 'is', 'go']
            },
            'position': 1,
            'start': 3
        },
        'word insertion (right, 1st substitution)': {
            'tokens': ('school', 'highest'),
            'lemmas': ('school', 'high'),
            'source': {
                'tokens': ['hell', 'now', 'this', 'is', 'school', 'boy'],
                'lemmas': ['hell', 'now', 'this', 'be', 'school', 'boy']
            },
            'destination': {
                'tokens': ['this', 'is', 'highest', 'school'],
                'lemmas': ['this', 'be', 'high', 'school']
            },
            'position': 2,
            'start': 2
        },
        'word insertion (right, 2nd substitution)': {
            'tokens': ('boy', 'school'),
            'lemmas': ('boy', 'school'),
            'source': {
                'tokens': ['hell', 'now', 'this', 'is', 'school', 'boy'],
                'lemmas': ['hell', 'now', 'this', 'be', 'school', 'boy']
            },
            'destination': {
                'tokens': ['this', 'is', 'highest', 'school'],
                'lemmas': ['this', 'be', 'high', 'school']
            },
            'position': 3,
            'start': 2
        },
        'word insertion (left, 1st substitution)': {
            'tokens': ('boy', 'highest'),
            'lemmas': ('boy', 'high'),
            'source': {
                'tokens': ['hell', 'now', 'boy', 'highest', 'is', 'the',
                           'best', 'thing'],
                'lemmas': ['hell', 'now', 'boy', 'high', 'be', 'the',
                           'best', 'thing']
            },
            'destination': {
                'tokens': ['highest', 'school', 'is', 'the', 'best', 'thing'],
                'lemmas': ['high', 'school', 'be', 'the', 'best', 'thing']
            },
            'position': 0,
            'start': 2
        },
        'word insertion (left, 2nd substitution)': {
            'tokens': ('highest', 'school'),
            'lemmas': ('high', 'school'),
            'source': {
                'tokens': ['hell', 'now', 'boy', 'highest', 'is', 'the',
                           'best', 'thing'],
                'lemmas': ['hell', 'now', 'boy', 'high', 'be', 'the',
                           'best', 'thing']
            },
            'destination': {
                'tokens': ['highest', 'school', 'is', 'the', 'best', 'thing'],
                'lemmas': ['high', 'school', 'be', 'the', 'best', 'thing']
            },
            'position': 1,
            'start': 2
        },
        'words stuck together (right, 1st substitution)': {
            'tokens': ('policy', 'policymakers'),
            'lemmas': ('policy', 'policymaker'),
            'source': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policymakers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policymaker', 'plate']
            },
            'position': 3,
            'start': 0
        },
        'words stuck together (right, 2nd substitution)': {
            'tokens': ('makers', 'plate'),
            'lemmas': ('maker', 'plate'),
            'source': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policymakers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policymaker', 'plate']
            },
            'position': 4,
            'start': 0
        },
        'words stuck together (right, hyphen, 1st substitution)': {
            'tokens': ('policy', 'policy-makers'),
            'lemmas': ('policy', 'policy-maker'),
            'source': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy-makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy-maker', 'plate']
            },
            'position': 3,
            'start': 0
        },
        'words stuck together (right, hyphen, 2nd substitution)': {
            'tokens': ('makers', 'plate'),
            'lemmas': ('maker', 'plate'),
            'source': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy-makers', 'plate'],
                'lemmas': ['this', 'be', 'the', 'policy-maker', 'plate']
            },
            'position': 4,
            'start': 0
        },
        'words stuck together (left, 1st substitution)': {
            'tokens': ('better', 'think'),
            'lemmas': ('better', 'think'),
            'source': {
                'tokens': ['i', 'think', 'better', 'time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better', 'time', 'do', 'do']
            },
            'destination': {
                'tokens': ['think', 'bettertime', 'will', 'do'],
                'lemmas': ['think', 'bettertime', 'do', 'do']
            },
            'position': 0,
            'start': 2
        },
        'words stuck together (left, 2nd substitution)': {
            'tokens': ('time', 'bettertime'),
            'lemmas': ('time', 'bettertime'),
            'source': {
                'tokens': ['i', 'think', 'better', 'time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better', 'time', 'do', 'do']
            },
            'destination': {
                'tokens': ['think', 'bettertime', 'will', 'do'],
                'lemmas': ['think', 'bettertime', 'do', 'do']
            },
            'position': 1,
            'start': 2
        },
        'words stuck together (left, hyphen, 1st substitution)': {
            'tokens': ('better', 'think'),
            'lemmas': ('better', 'think'),
            'source': {
                'tokens': ['i', 'think', 'better', 'time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better', 'time', 'do', 'do']
            },
            'destination': {
                'tokens': ['think', 'better-time', 'will', 'do'],
                'lemmas': ['think', 'better-time', 'do', 'do']
            },
            'position': 0,
            'start': 2
        },
        'words stuck together (left, hyphen, 2nd substitution)': {
            'tokens': ('time', 'better-time'),
            'lemmas': ('time', 'better-time'),
            'source': {
                'tokens': ['i', 'think', 'better', 'time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better', 'time', 'do', 'do']
            },
            'destination': {
                'tokens': ['think', 'better-time', 'will', 'do'],
                'lemmas': ['think', 'better-time', 'do', 'do']
            },
            'position': 1,
            'start': 2
        },
        'words separated (right, 1st substitution)': {
            'tokens': ('policymakers', 'policy'),
            'lemmas': ('policymaker', 'policy'),
            'source': {
                'tokens': ['hell', 'now', 'these', 'are', 'the',
                           'policymakers', 'plate'],
                'lemmas': ['hell', 'now', 'this', 'be', 'the',
                           'policymaker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker']
            },
            'position': 3,
            'start': 2
        },
        'words separated (right, 2nd substitution)': {
            'tokens': ('plate', 'makers'),
            'lemmas': ('plate', 'maker'),
            'source': {
                'tokens': ['hell', 'now', 'these', 'are', 'the',
                           'policymakers', 'plate'],
                'lemmas': ['hell', 'now', 'this', 'be', 'the',
                           'policymaker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker']
            },
            'position': 4,
            'start': 2
        },
        'words separated (right, hyphen, 1st substitution)': {
            'tokens': ('policy-makers', 'policy'),
            'lemmas': ('policy-maker', 'policy'),
            'source': {
                'tokens': ['hell', 'now', 'these', 'are', 'the',
                           'policy-makers', 'plate'],
                'lemmas': ['hell', 'now', 'this', 'be', 'the',
                           'policy-maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker']
            },
            'position': 3,
            'start': 2
        },
        'words separated (right, hyphen, 2nd substitution)': {
            'tokens': ('plate', 'makers'),
            'lemmas': ('plate', 'maker'),
            'source': {
                'tokens': ['hell', 'now', 'these', 'are', 'the',
                           'policy-makers', 'plate'],
                'lemmas': ['hell', 'now', 'this', 'be', 'the',
                           'policy-maker', 'plate']
            },
            'destination': {
                'tokens': ['these', 'are', 'the', 'policy', 'makers'],
                'lemmas': ['this', 'be', 'the', 'policy', 'maker']
            },
            'position': 4,
            'start': 2
        },
        'words separated (left, 1st substitution)': {
            'tokens': ('think', 'better'),
            'lemmas': ('think', 'better'),
            'source': {
                'tokens': ['i', 'think', 'bettertime', 'will', 'do'],
                'lemmas': ['i', 'think', 'bettertime', 'do', 'do']
            },
            'destination': {
                'tokens': ['better', 'time', 'will', 'do'],
                'lemmas': ['better', 'time', 'do', 'do']
            },
            'position': 0,
            'start': 1
        },
        'words separated (left, 2nd substitution)': {
            'tokens': ('bettertime', 'time'),
            'lemmas': ('bettertime', 'time'),
            'source': {
                'tokens': ['i', 'think', 'bettertime', 'will', 'do'],
                'lemmas': ['i', 'think', 'bettertime', 'do', 'do']
            },
            'destination': {
                'tokens': ['better', 'time', 'will', 'do'],
                'lemmas': ['better', 'time', 'do', 'do']
            },
            'position': 1,
            'start': 1
        },
        'words separated (left, hyphen, 1st substitution)': {
            'tokens': ('think', 'better'),
            'lemmas': ('think', 'better'),
            'source': {
                'tokens': ['i', 'think', 'better-time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better-time', 'do', 'do']
            },
            'destination': {
                'tokens': ['better', 'time', 'will', 'do'],
                'lemmas': ['better', 'time', 'do', 'do']
            },
            'position': 0,
            'start': 1
        },
        'words separated (left, hyphen, 2nd substitution)': {
            'tokens': ('better-time', 'time'),
            'lemmas': ('better-time', 'time'),
            'source': {
                'tokens': ['i', 'think', 'better-time', 'will', 'do'],
                'lemmas': ['i', 'think', 'better-time', 'do', 'do']
            },
            'destination': {
                'tokens': ['better', 'time', 'will', 'do'],
                'lemmas': ['better', 'time', 'do', 'do']
            },
            'position': 1,
            'start': 1
        },
    },
    True: {
        'all good 1': {
            'tokens': ('hello', 'goodbye'),
            'lemmas': ('hello', 'goodbye'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        },
        'all good 2': {
            'tokens': ('tree', 'band'),
            'lemmas': ('tree', 'bush'),
            'source': {'tokens': [], 'lemmas': []},
            'destination': {'tokens': [], 'lemmas': []},
            'position': 0,
            'start': 0
        }
    }
}


validator_mixin_params = [
    (success, title)
    for success, success_cases in validator_mixin_cases.items()
    for title in success_cases.keys()
]


@pytest.mark.parametrize('success,title', validator_mixin_params,
                         ids=['{}'.format(param)
                              for param in validator_mixin_params])
def test_substitution_validator_mixin(success, title):
    props = validator_mixin_cases[success][title]

    svm = SubstitutionValidatorMixin()
    svm.tokens = props['tokens']
    svm.lemmas = props['lemmas']
    svm.source = Namespace({
        'tokens': props['source']['tokens'],
        'lemmas': props['source']['lemmas']
    })
    svm.destination = Namespace({
        'tokens': props['destination']['tokens'],
        'lemmas': props['destination']['lemmas']
    })
    svm.position = props['position']
    svm.start = props['start']
    assert svm.validate() == success


substitutions_cases = {
    # Time.discrete, some basic checks
    (Time.discrete, Source.all, Past.last_bin, Durl.all, 1): {
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6}
            ]
        },
        'two substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest='2008-07-30 02:00:00',
                                           dest_other1='2008-08-01 00:00:00',
                                           dest_other2='2008-08-01 05:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 2, 'position': 6}
            ]
        },
        'three substitutions': {
            'content': raw_cluster5.format(source='2008-07-31 00:00:00',
                                           dest='2008-08-01 02:00:00',
                                           dest_other1='2008-08-01 06:00:00',
                                           dest_other2='2008-08-01 22:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 2, 'position': 6}
            ]
        }
    },
    # Time.continuous, majority effects
    (Time.continuous, Source.majority, Past.last_bin, Durl.all, 1): {
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
                {'source_sid': 2, 'destination_sid': 1,
                 'occurrence': 1, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
                {'source_sid': 2, 'destination_sid': 1,
                 'occurrence': 2, 'position': 6},
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
                {'source_sid': 2, 'destination_sid': 1,
                 'occurrence': 1, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
            ]
        }
    },
    # Time.continuous past exclusion (from last_bin)
    (Time.continuous, Source.all, Past.last_bin, Durl.exclude_past, 1): {
        'one substitution': {
            'content': raw_cluster5.format(source='2008-07-31 02:00:00',
                                           dest_other1='2008-07-30 23:00:00',
                                           dest='2008-08-01 00:00:00',
                                           dest_other2='2008-08-01 01:00:00'),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
            ]
        },
    },
    # Time.continuous past exclusion (from all)
    (Time.continuous, Source.all, Past.all, Durl.exclude_past, 1): {
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
            ]
        },
    },
    # Time.discrete majority effect and past exclusion
    (Time.discrete, Source.majority, Past.last_bin, Durl.exclude_past, 1): {
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
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 6},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 1, 'position': 6},
            ]
        }
    },
    # Time discrete, double substitutions
    (Time.discrete, Source.majority, Past.last_bin, Durl.all, 2): {
        'one substitution': {
            'content': raw_cluster7.format(
                source='2008-07-30 02:00:00',
                source_string="she jumped over the cat",
                dest='2008-07-31 02:00:00',
                dest_string="she walked over the cat"
            ),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 1}
            ]
        },
        'two substitutions': {
            'content': raw_cluster7.format(
                source='2008-07-30 02:00:00',
                source_string="she jumped over the cat",
                dest='2008-07-31 02:00:00',
                dest_string="she walked over the dog"
            ),
            'substitutions': [
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 1},
                {'source_sid': 1, 'destination_sid': 2,
                 'occurrence': 0, 'position': 4}
            ]
        },
        'no substitutions (too many)': {
            'content': raw_cluster7.format(
                source='2008-07-30 02:00:00',
                source_string="she jumped over the cat's tail",
                dest='2008-07-31 02:00:00',
                dest_string="she walked over the dog's fur"
            ),
            'substitutions': []
        }
    }
}


substitutions_params = [
    (time, source, past, durl, max_distance, string)
    for (time, source, past, durl, max_distance), model_cases
    in substitutions_cases.items()
    for string in model_cases.keys()
]


@pytest.fixture(params=substitutions_params,
                ids=['{}'.format(param) for param in substitutions_params])
def substitutions_db(request, tmpdb):
    time, source, past, durl, max_distance, string = request.param
    content = substitutions_cases[
        (time, source, past, durl, max_distance)][string]['content']
    expected_substitutions = substitutions_cases[
        (time, source, past, durl, max_distance)][string]['substitutions']
    load_db(header + content)
    return (Model(time, source, past, durl, max_distance),
            expected_substitutions)


def test_cluster_miner_mixin_substitutions(substitutions_db):
    model, expected_substitutions = substitutions_db

    with session_scope() as session:
        cluster = session.query(Cluster).filter_by(sid=1).one()
        substitutions = sorted((s.source.sid, s.destination.sid,
                                s.occurrence, s.position)
                               for s in cluster.substitutions(model))
        assert substitutions == sorted((s['source_sid'], s['destination_sid'],
                                        s['occurrence'], s['position'])
                                       for s in expected_substitutions)


mine_substitutions_content = (
    '''
3\t8\tit's real that i love fooling\t1'''
    # The first part of this cluster defines basic substitutions,
    # simple and double.
    '''
\t4\t3\tit's real that i love fooling\t1
\t\t2008-07-31 00:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t2\tB\tsome-url

\t3\t2\tit's real that i adore playing\t2
\t\t2008-07-31 08:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t2\tB\tsome-url
'''
    # This substitution here will not validate() ('foo' abbreviates 'fooling'),
    # and we're making sure the non-validation doesn't wipe out the previously
    # detected substitutions.
    '''
\t1\t1\tit's real that i love foo\t3
\t\t2008-08-02 07:00:00\t1\tB\tsome-url
'''
    # Change of majority quote.
    '''
2\t6\tit's real that i love fooling\t2
\t4\t4\tit's real that i love fooling\t4
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love playing\t5
\t\t2008-07-31 10:00:00\t1\tB\tsome-url
\t\t2008-08-01 00:00:00\t1\tB\tsome-url
'''
    # Majority masquing.
    '''
3\t10\tit's real that i love fooling\t3
\t4\t4\tit's real that i love fooling\t6
\t\t2008-07-31 09:00:00\t1\tM\tsome-url
\t\t2008-07-31 16:00:00\t1\tB\tsome-url
\t\t2008-07-31 18:00:00\t1\tB\tsome-url
\t\t2008-08-01 08:00:00\t1\tB\tsome-url

\t2\t2\tit's real that i love playing\t7
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
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 0, 'position': 5},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 0, 'position': 6},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 1, 'position': 5},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 1, 'position': 6},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 1, 'position': 5},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 1, 'position': 6},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 2, 'position': 5},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 2, 'position': 6},
            # Cluster 2.
            {'source_sid': 4, 'destination_sid': 5,
             'occurrence': 0, 'position': 6},
            {'source_sid': 5, 'destination_sid': 4,
             'occurrence': 1, 'position': 6},
            {'source_sid': 4, 'destination_sid': 5,
             'occurrence': 1, 'position': 6},
            # Cluster 3.
            {'source_sid': 6, 'destination_sid': 7,
             'occurrence': 0, 'position': 6}
            # Cluster 4: nothing (filtered out).
        ]
    },
    'with limit': {
        'limit': 1,
        'substitutions': [
            # Cluster 1.
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 0, 'position': 5},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 0, 'position': 6},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 1, 'position': 5},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 1, 'position': 6},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 1, 'position': 5},
            {'source_sid': 1, 'destination_sid': 2,
             'occurrence': 1, 'position': 6},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 2, 'position': 5},
            {'source_sid': 2, 'destination_sid': 1,
             'occurrence': 2, 'position': 6},
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
    model = Model(Time.continuous, Source.majority, Past.last_bin, Durl.all, 2)
    mine_substitutions_with_model(model, limit=limit)

    # Test.
    with session_scope() as session:
        substitutions = sorted((s.source.sid, s.destination.sid,
                                s.occurrence, s.position)
                               for s in session.query(Substitution))
        print(substitutions)
        print(sorted((s['source_sid'], s['destination_sid'],
                      s['occurrence'], s['position'])
                     for s in expected_substitutions))
        assert substitutions == sorted((s['source_sid'], s['destination_sid'],
                                        s['occurrence'], s['position'])
                                       for s in expected_substitutions)

    # Check we can't mine again with the same model.
    with pytest.raises(Exception) as excinfo:
        mine_substitutions_with_model(model, limit=limit)
    assert 'contains substitutions mined with this model' in str(excinfo.value)
    # But it's ok with another model.
    mine_substitutions_with_model(Model(Time.discrete, Source.majority,
                                        Past.last_bin, Durl.all, 2),
                                  limit=limit)
