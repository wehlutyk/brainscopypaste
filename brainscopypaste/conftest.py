from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Base, Session, Cluster, Quote, Url


@pytest.fixture
def tmpdb():
    engine = create_engine('sqlite:///:memory:')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)


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
        session.add_all(Quote(sid=i,
                              cluster=clusters.filter_by(sid=i % 5).one(),
                              string='Some quote to tokenize {}'.format(i))
                        for i in sids)

    return sids


@pytest.fixture
def some_urls(some_clusters, some_quotes):
    ids = range(20)
    with session_scope() as session:
        quotes = session.query(Quote)
        session.add_all(Url(id=i,
                            quote=quotes.filter_by(sid=i % 10).one(),
                            timestamp=datetime.utcnow() + timedelta(days=i),
                            frequency=2,
                            url_type='B',
                            url='Url {}'.format(i))
                        for i in ids)

    return ids
