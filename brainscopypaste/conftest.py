from datetime import datetime

import pytest
from sqlalchemy import create_engine

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Base, Session, Cluster, Quote, Url


@pytest.fixture
def tmpdb():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def some_clusters(tmpdb):
    ids = range(5)
    with session_scope() as session:
        session.add_all(Cluster(id=i, source='test') for i in ids)

    return ids


@pytest.fixture
def some_quotes(some_clusters):
    ids = range(10)
    with session_scope() as session:
        clusters = session.query(Cluster)
        session.add_all(Quote(id=i,
                              cluster=clusters.get(i % 5),
                              string='Quote {}'.format(i))
                        for i in ids)

    return ids


@pytest.fixture
def some_urls(some_clusters, some_quotes):
    ids = range(20)
    with session_scope() as session:
        quotes = session.query(Quote)
        session.add_all(Url(id=i,
                            quote=quotes.get(i % 10),
                            timestamp=datetime.utcnow(),
                            frequency=2,
                            url_type='B',
                            url='Url {}'.format(i))
                        for i in ids)

    return ids
