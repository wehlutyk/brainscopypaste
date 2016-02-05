import os
from tempfile import mkstemp
from datetime import datetime

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


def test_model_init():
    with pytest.raises(AssertionError):
        Model(1, Source.all, Past.all, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, 1, Past.all, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, 1, Durl.all)
    with pytest.raises(AssertionError):
        Model(Time.continuous, Source.all, Past.all, 1)


def load_db(content):
    fd, filepath = mkstemp()
    with open(fd, 'w') as tmp:
        tmp.write(content)

    line_count = content.count('\n') + 1
    MemeTrackerParser(filepath, line_count=line_count).parse()
    os.remove(filepath)


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


contents_base = {
    (Time.continuous, Past.all): {
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
    (Time.continuous, Past.last_bin): {
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
    (Time.discrete, Past.all): {
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
    (Time.discrete, Past.last_bin): {
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
    },
}


params_base = [(time, past, success, string)
               for ((time, past), time_past) in contents_base.items()
               for (success, contents) in time_past.items()
               for string in contents.keys()]


@pytest.fixture(params=params_base,
                ids=['{}'.format(param) for param in params_base])
def content_base(request, tmpdb):
    time, past, success, string = request.param
    load_db(header + contents_base[(time, past)][success][string])
    return time, past, success


def assert_validation(validate, success):
    with session_scope() as session:
        source = session.query(Quote).filter_by(sid=1).one()
        dest = session.query(Quote).filter_by(sid=2).one()
        assert validate(source, dest.urls[0]) == success


def test_model_validate_base(content_base):
    time, past, success = content_base
    model = Model(time, Source.all, past, Durl.all)
    assert_validation(model._validate_base, success)
