from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote, Url


def test_cluster(some_clusters):
    with session_scope() as session:
        assert session.query(Cluster).count() == 5
        assert session.query(Cluster.id).all() == [(i,) for i in some_clusters]


def test_quote(some_quotes):
    with session_scope() as session:
        assert session.query(Quote).count() == 10

        assert session.query(Quote).get(0).cluster.id == 0
        assert session.query(Quote).get(2).cluster.id == 2
        assert session.query(Quote).get(4).cluster.id == 4
        assert session.query(Quote).get(6).cluster.id == 1

        assert [quote.id
                for quote in session.query(Cluster).get(3).quotes] == [3, 8]
        q1 = session.query(Quote).get(1)
        assert session.query(Cluster.id)\
            .filter(Cluster.quotes.contains(q1)).one() == (1,)
        q7 = session.query(Quote).get(7)
        assert session.query(Cluster.id)\
            .filter(Cluster.quotes.contains(q7)).one() == (2,)

        assert session.query(Quote).get(0).size == 0
        assert session.query(Quote).get(0).frequency == 0
        assert session.query(Cluster).get(3).size == 2
        assert session.query(Cluster).get(3).frequency == 0


def test_url(some_urls):
    with session_scope() as session:
        assert session.query(Url).count() == 20

        assert session.query(Url).get(2).quote.id == 2
        assert session.query(Url).get(2).cluster.id == 2
        assert session.query(Url).get(6).quote.id == 6
        assert session.query(Url).get(6).cluster.id == 1
        assert session.query(Url).get(10).quote.id == 0
        assert session.query(Url).get(10).cluster.id == 0
        assert session.query(Url).get(17).quote.id == 7
        assert session.query(Url).get(17).cluster.id == 2

        assert session.query(Url).get(0).timestamp - datetime.utcnow() < \
            timedelta(seconds=5)

        assert session.query(Quote).get(0).size == 2
        assert session.query(Quote).get(0).frequency == 4
        assert [url.id for url in session.query(Quote).get(1).urls] == [1, 11]
        assert session.query(Cluster).get(0).size == 2
        assert session.query(Cluster).get(0).frequency == 8

    with pytest.raises(IntegrityError):
        with session_scope() as session:
            quote = session.query(Quote).get(1)
            session.add(Url(quote=quote,
                            timestamp=datetime.now(),
                            frequency=1,
                            url_type='C',
                            url='some url'))
