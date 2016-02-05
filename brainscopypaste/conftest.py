from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Base, Session, Cluster, Quote, Url, Substitution
from brainscopypaste.mine import Model, Time, Source, Past, Durl


@pytest.fixture
def tmpdb(request):
    engine = create_engine('postgresql+psycopg2://brainscopypaste:'
                           '@localhost:5432/brainscopypaste_test',
                           client_encoding='utf8')
    Session.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    def fin():
        Base.metadata.drop_all(engine)

    request.addfinalizer(fin)


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
    with session_scope() as session:
        cluster = session.query(Cluster).filter_by(sid=0).one()
        q10 = Quote(sid=10, cluster=cluster,
                    string="Don't do it! I know I wouldn't")
        q11 = Quote(sid=11, cluster=cluster, string="I know I hadn't")
        session.add(q10)
        session.add(q11)
        model = Model(Time.discrete, Source.majority, Past.last_bin, Durl.all)
        s = Substitution(source=q10, destination=q11,
                         occurrence=0, start=5,
                         position=3, model=model)
        session.add(s)
