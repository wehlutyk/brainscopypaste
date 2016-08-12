"""Test fixtures.

"""


from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Base, Session, Cluster, Quote, Url, Substitution
from brainscopypaste.mine import Model, Time, Source, Past, Durl


@pytest.yield_fixture
def tmpdb():
    engine = create_engine('postgresql+psycopg2://brainscopypaste:'
                           '@localhost:5432/brainscopypaste_test',
                           client_encoding='utf8')
    Session.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def some_clusters(tmpdb):
    sids = range(5)
    with session_scope() as session:
        session.add_all(Cluster(sid=i, source='test') for i in sids)

    return sids


@pytest.fixture
def some_quotes(some_clusters):
    sids = range(10)
    with session_scope() as session:
        clusters = session.query(Cluster)
        # Insert quotes in reverse order to check ordering
        session.add_all(Quote(sid=i,
                              cluster=clusters.filter_by(sid=i % 5).one(),
                              string='Some quote to tokenize {}'.format(i))
                        for i in sids[::-1])

    return sids


@pytest.fixture
def some_urls(some_clusters, some_quotes):
    ids = range(20)
    with session_scope() as session:
        quotes = session.query(Quote)
        # Insert urls in reverse order to check ordering
        for i in ids[::-1]:
            quotes.filter_by(sid=i % 10).one()\
                .add_url(Url(timestamp=(datetime(year=2008, month=1, day=1) +
                                        timedelta(days=i)),
                             frequency=2, url_type='B',
                             url='Url with " and \' {}'.format(i)))

    return ids


@pytest.fixture
def some_substitutions(some_clusters, some_quotes, some_urls):
    model1 = Model(Time.discrete, Source.majority, Past.last_bin, Durl.all, 1)
    model2 = Model(Time.discrete, Source.majority, Past.all, Durl.all, 1)
    with session_scope() as session:
        c0 = session.query(Cluster).filter_by(sid=0).one()
        c1 = session.query(Cluster).filter_by(sid=1).one()
        q10 = Quote(sid=10, cluster=c0,
                    string="Don't do it! I know I wouldn't")
        q11 = Quote(sid=11, cluster=c0, string="I know I hadn't")
        q12 = Quote(sid=12, cluster=c0, string="some string")
        q13 = Quote(sid=13, cluster=c0, string="some other string")
        q14 = Quote(sid=14, cluster=c1, string="some other string 2")
        q15 = Quote(sid=15, cluster=c1, string="some other string 3")
        session.add(q10)
        session.add(q11)
        session.add(q12)
        session.add(q13)
        session.add(q14)
        session.add(q15)
        session.add(Substitution(source=q10, destination=q11,
                                 occurrence=0, start=5,
                                 position=3, model=model1))
        # Same durl (destination, occurrence) as above, but different source,
        # different start and different destination position.
        session.add(Substitution(source=q12, destination=q11,
                                 occurrence=0, start=2,
                                 position=2, model=model1))
        # Same destination but different occurrence (so different durl).
        session.add(Substitution(source=q13, destination=q11,
                                 occurrence=1, start=5,
                                 position=3, model=model1))
        # Different destination altogether.
        session.add(Substitution(source=q13, destination=q12,
                                 occurrence=0, start=0,
                                 position=1, model=model2))
        # Different cluster.
        session.add(Substitution(source=q14, destination=q15,
                                 occurrence=0, start=0,
                                 position=1, model=model2))

    return model1, model2
