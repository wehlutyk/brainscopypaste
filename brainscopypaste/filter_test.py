"""Tests for :mod:`.filter`.

"""


from datetime import datetime, timedelta

import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import Cluster, Quote, Url
from brainscopypaste.filter import (AlreadyFiltered, filter_clusters, _top_id,
                                    filter_cluster_offset, filter_quote_offset)


@pytest.fixture
def filterable_cluster(tmpdb):
    with session_scope() as session:
        cluster = Cluster(sid=0, source='test')
        cluster.quotes = [
            # Quote 0 is good.
            Quote(sid=0, string='a string with enough words and no problems'),
            # Quote 1 has not enough words.
            Quote(sid=1, string='not enough words here'),
            # Quote 2 is not in English.
            Quote(sid=2, string="ceci n'est pas de l'anglais "
                                "mais a assez de mots"),
            # Quote 3 spans too long.
            Quote(sid=3, string="a quote that spans too long"),
            # Quote 4 has no urls at all.
            Quote(sid=4, string="a quote without any urls")
        ]
        # Quote 0 is good.
        cluster.quotes[0].add_urls([
            Url(timestamp=datetime.utcnow(), frequency=2,
                url_type='M', url='some-url'),
            Url(timestamp=datetime.utcnow() + timedelta(days=80, hours=-1),
                frequency=2, url_type='M', url='some-url')
        ])
        # Quote 1 has not enough words.
        cluster.quotes[1].add_urls([
            Url(timestamp=datetime.utcnow(), frequency=2,
                url_type='M', url='some-url')
        ])
        # Quote 2 is not in English.
        cluster.quotes[2].add_urls([
            Url(timestamp=datetime.utcnow(), frequency=2,
                url_type='M', url='some-url')
        ])
        # Quote 3 spans too long.
        cluster.quotes[3].add_urls([
            Url(timestamp=datetime.utcnow(), frequency=2,
                url_type='M', url='some-url'),
            Url(timestamp=datetime.utcnow() + timedelta(days=80, hours=1),
                frequency=2, url_type='M', url='some-url')
        ])
        # Quote 4 has no urls at all.

        # Save all this.
        session.add(cluster)


def test_cluster_kept(filterable_cluster):
    # Our cluster gets all its quotes filtered out but one (#0),
    # and is then kept.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        fcluster = cluster.filter()

        assert fcluster.size == 1
        assert fcluster.quotes.first().sid == 0


def test_filter_clusters_kept(filterable_cluster):
    # Our cluster gets all its quotes filtered out but one (#0),
    # and is then kept.
    filter_clusters()
    with session_scope() as session:
        fcluster = session.query(Cluster)\
            .filter(Cluster.filtered.is_(True)).one()
        assert fcluster.size == 1
        assert fcluster.quotes.first().sid == 0


def test_filter_clusters_limit(filterable_cluster):
    # Our cluster gets all its quotes filtered out but one (#0),
    # and is then kept.
    filter_clusters(limit=0)
    with session_scope() as session:
        assert session.query(Cluster)\
            .filter(Cluster.filtered.is_(True)).count() == 0

    filter_clusters(limit=1)
    with session_scope() as session:
        fcluster = session.query(Cluster)\
            .filter(Cluster.filtered.is_(True)).one()
        assert fcluster.size == 1
        assert fcluster.quotes.first().sid == 0


def test_cluster_emptied(filterable_cluster):
    # Modify our cluster to make it bad.
    with session_scope() as session:
        quote = session.query(Quote).filter(Quote.sid == 0).one()
        timestamps = quote.url_timestamps.copy()
        timestamps[1] = datetime.utcnow() + timedelta(days=81)
        quote.url_timestamps = timestamps

    # Now check our cluster gets filtered out.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        assert cluster.filter() is None


def test_filter_clusters_emptied(filterable_cluster):
    # Modify our cluster to make it bad.
    with session_scope() as session:
        quote = session.query(Quote).filter(Quote.sid == 0).one()
        timestamps = quote.url_timestamps.copy()
        timestamps[1] = datetime.utcnow() + timedelta(days=81)
        quote.url_timestamps = timestamps

    # Check our cluster gets filtered out.
    filter_clusters()
    with session_scope() as session:
        assert session.query(Cluster)\
            .filter(Cluster.filtered.is_(True)).count() == 0


def test_cluster_too_long(filterable_cluster):
    # Modify our cluster to make it too long after quote filtering.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        # This quote is all good, but is too far from quote sid=0, leading
        # the cluster span to be too long.
        quote = Quote(sid=5, string='a string with enough '
                                    'words and no problems')
        quote.add_url(
            Url(timestamp=datetime.utcnow() + timedelta(days=80, hours=1),
                frequency=2, url_type='M', url='some-url')
        )
        cluster.quotes.append(quote)

    # Now check our cluster gets filtered out.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        assert cluster.filter() is None


def test_filter_clusters_too_long(filterable_cluster):
    # Modify our cluster to make it too long after quote filtering.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        # This quote is all good, but is too far from quote sid=0, leading
        # the cluster span to be too long.
        quote = Quote(sid=5, string='a string with enough '
                                    'words and no problems')
        quote.add_url(
            Url(timestamp=datetime.utcnow() + timedelta(days=80, hours=1),
                frequency=2, url_type='M', url='some-url')
        )
        cluster.quotes.append(quote)

    # Now check our cluster gets filtered out.
    filter_clusters()
    with session_scope() as session:
        assert session.query(Cluster)\
            .filter(Cluster.filtered.is_(True)).count() == 0


def test_cluster_already_filtered(filterable_cluster):
    # Filter our good cluster.
    with session_scope() as session:
        cluster = session.query(Cluster).first()
        fcluster = cluster.filter()
        session.add(fcluster)

    # Add check we can't filter it again.
    with pytest.raises(AlreadyFiltered):
        with session_scope() as session:
            fcluster = session.merge(fcluster)
            fcluster.filter()


def test_filter_clusters_already_filtered(filterable_cluster):
    # Filter our good cluster.
    filter_clusters()

    # Add check we can't filter it again.
    with pytest.raises(AlreadyFiltered):
        filter_clusters()


def test_top_id():
    assert _top_id(1) == 1000
    assert _top_id(10) == 10000
    assert _top_id(25) == 10000
    assert _top_id(75) == 10000
    assert _top_id(100) == 100000


def test_filter_cluster_offset_1(filterable_cluster):
    # With one unfiltered cluster.
    filter_cluster_offset.drop_cache()
    assert filter_cluster_offset() == 1000


def test_filter_cluster_offset_2(some_clusters):
    # With five unfiltered cluster.
    filter_cluster_offset.drop_cache()
    assert filter_cluster_offset() == 1000


def test_filter_quote_offset(some_quotes):
    # With ten unfiltered quotes.
    filter_quote_offset.drop_cache()
    assert filter_quote_offset() == 10000
