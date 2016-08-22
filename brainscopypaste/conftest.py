"""Test fixtures used throughout the whole test suite.

Use any of these functions if you need a boilerplate database with clusters,
quotes, urls, and substitutions to test code on. Refer to `pytest's
documentation <http://docs.pytest.org/en/latest/>`_ for more information on
fixtures and how to use them in test code.

"""


from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Base, Session, Cluster, Quote, Url, Substitution
from brainscopypaste.mine import Model, Time, Source, Past, Durl


@pytest.yield_fixture
def tmpdb():
    """Get a handle to an empty temporary database that is wiped on
    teardown."""

    from brainscopypaste.conf import settings
    engine = create_engine(
        'postgresql+psycopg2://{user}:{pw}@localhost:5432/{db}'
        .format(user=settings.DB_USER, pw=settings.DB_PASSWORD,
                db=settings.DB_NAME_TEST),
        client_encoding='utf8')
    Session.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def some_clusters(tmpdb):
    """Get a handle to a temporary database filled with a few empty clusters,
    wiped on teardown.

    See the source code if you need details on the clusters' exact attributes.

    """

    sids = range(5)
    with session_scope() as session:
        session.add_all(Cluster(sid=i, source='test') for i in sids)

    return sids


@pytest.fixture
def some_quotes(some_clusters):
    """Get a handle to a temporary database filled with a few clusters and
    quotes, wiped on teardown.

    See the source code if you need details on the clusters' and quotes' exact
    attributes.

    """

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
    """Get a handle to a temporary database filled with a few clusters, quotes,
    and urls, all wiped on teardown.

    See the source code if you need details on the clusters', quotes', and
    urls' exact attributes.

    """

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
    """Get a handle to a temporary database filled with a few clusters, quotes,
    urls, and substitutions all wiped on teardown.

    The substitutions are assigned to two different substitution models
    (although their actual occurrences don't fit with those models).

    See the source code if you need details on the clusters', quotes', and
    urls' exact attributes.

    """

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
