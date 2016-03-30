from datetime import datetime, timedelta

from sqlalchemy.exc import DataError
import pytest

from brainscopypaste.utils import session_scope
from brainscopypaste.db import (Cluster, Quote, Url, Substitution,
                                SealedException)
from brainscopypaste.mine import Model, Past, Source, Time, Durl


def test_cluster(some_clusters):
    # Test empty cluster attributes.
    cluster = Cluster()
    assert cluster.size == 0
    assert cluster.size_urls == 0
    assert cluster.frequency == 0
    with pytest.raises(ValueError) as excinfo:
        cluster.span
    assert 'No urls' in str(excinfo.value)
    assert cluster.urls == []

    # Test clusters from database.
    with session_scope() as session:
        assert session.query(Cluster).count() == 5
        assert session.query(Cluster.sid).all() == \
            [(i,) for i in some_clusters]
        assert session.query(Cluster).filter_by(sid=0).one().size == 0
        assert session.query(Cluster).filter_by(sid=0).one().size_urls == 0
        assert session.query(Cluster).filter_by(sid=0).one().frequency == 0
        with pytest.raises(ValueError) as excinfo:
            session.query(Cluster).filter_by(sid=0).one().span
        assert 'No urls' in str(excinfo.value)
        assert session.query(Cluster).filter_by(sid=0).one().urls == []

        assert session.query(Cluster).get(1).format_copy() == \
            '1\t0\tFalse\ttest'


def test_quote(some_quotes):
    # Test empty quote attributes.
    quote = Quote()
    assert quote.size == 0
    assert quote.frequency == 0
    with pytest.raises(ValueError) as excinfo:
        quote.span
    assert 'No urls' in str(excinfo.value)
    assert quote.urls == []
    with pytest.raises(ValueError) as excinfo:
        quote.tags
    assert 'No string' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        quote.tokens
    assert 'No string' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        quote.lemmas
    assert 'No string' in str(excinfo.value)

    # Test quotes from database.
    with session_scope() as session:
        assert session.query(Quote).count() == 10

        assert session.query(Quote).filter_by(sid=0).one().cluster.sid == 0
        assert session.query(Quote).filter_by(sid=2).one().cluster.sid == 2
        assert session.query(Quote).filter_by(sid=4).one().cluster.sid == 4
        assert session.query(Quote).filter_by(sid=6).one().cluster.sid == 1
        assert session.query(Quote).filter_by(sid=6).one().tokens == \
            ('some', 'quote', 'to', 'tokenize', '6')
        assert session.query(Quote).filter_by(sid=6).one().tags == \
            ('DT', 'NN', 'TO', 'VV', 'CD')
        assert session.query(Quote).filter_by(sid=6).one().lemmas == \
            ('some', 'quote', 'to', 'tokenize', '6')

        assert set([quote.sid for quote in
                    session.query(Cluster).filter_by(sid=3).one().quotes]) == \
            set([3, 8])
        q1 = session.query(Quote).filter_by(sid=1).one()
        assert session.query(Cluster.sid)\
            .filter(Cluster.quotes.contains(q1)).one() == (1,)
        q7 = session.query(Quote).filter_by(sid=7).one()
        assert session.query(Cluster.sid)\
            .filter(Cluster.quotes.contains(q7)).one() == (2,)

        assert session.query(Quote).filter_by(sid=0).one().size == 0
        assert session.query(Quote).filter_by(sid=0).one().frequency == 0
        with pytest.raises(ValueError) as excinfo:
            session.query(Quote).filter_by(sid=0).one().span
        assert 'No urls' in str(excinfo.value)
        assert session.query(Quote).filter_by(sid=0).one().urls == []
        assert session.query(Cluster).filter_by(sid=3).one().size == 2
        assert session.query(Cluster).filter_by(sid=3).one().size_urls == 0
        assert session.query(Cluster).filter_by(sid=3).one().frequency == 0
        with pytest.raises(ValueError) as excinfo:
            session.query(Cluster).filter_by(sid=3).one().span
        assert 'No urls' in str(excinfo.value)

        q0 = session.query(Quote).filter_by(sid=0).one()
        assert q0.format_copy() == ('{}'.format(q0.id) +
                                    "\t1\t0\tFalse\tSome quote to "
                                    "tokenize 0\t{}\t{}\t{}\t{}")


def test_quote_add_url_sealed(some_quotes):
    with pytest.raises(SealedException):
        with session_scope() as session:
            u = Url(timestamp=datetime.utcnow(), frequency=1,
                    url_type='B', url='some url 1')
            q = session.query(Quote).filter_by(sid=0).one()
            assert q.size == len(q.urls)
            q.add_url(u)


def test_quote_add_urls_sealed(some_quotes):
    u1 = Url(timestamp=datetime.utcnow(), frequency=1,
             url_type='B', url='some url 1')
    u2 = Url(timestamp=datetime.utcnow(), frequency=1,
             url_type='B', url='some url 2')

    with pytest.raises(SealedException):
        with session_scope() as session:
            q = session.query(Quote).filter_by(sid=1).one()
            assert q.size == len(q.urls)
            q.add_urls([u1, u2])


def test_url(some_urls):
    with session_scope() as session:
        q0 = session.query(Quote).filter_by(sid=0).one()
        q3 = session.query(Quote).filter_by(sid=3).one()

        basedate = datetime(year=2008, month=1, day=1)
        assert q0.urls[0].timestamp == basedate
        assert q3.urls[0].timestamp == basedate + timedelta(days=3)

        assert q0.size == 2
        assert q0.frequency == 4
        assert q0.span == timedelta(days=10)

        assert q0.urls[0].occurrence == 0
        assert q0.urls[1].occurrence == 1
        assert q3.urls[0].occurrence == 0
        assert q3.urls[1].occurrence == 1

        c0 = session.query(Cluster).filter_by(sid=0).one()
        assert c0.size == 2
        assert c0.size_urls == 4
        assert c0.frequency == 8
        assert c0.span == timedelta(days=15)
        assert c0.urls[0].timestamp == basedate

        assert q0.format_copy() == \
            ('{}'.format(q0.id) +
             '\t1\t0\tFalse\tSome quote to tokenize 0\t'
             '{2008-01-01 00:00:00, 2008-01-11 00:00:00}\t'
             '{2, 2}\t{B, B}\t'
             '{"Url with \\\\" and \' 0", "Url with \\\\" and \' 10"}')

    with pytest.raises(DataError):
        with session_scope() as session:
            quote = session.query(Quote).filter_by(sid=1).one()
            quote.add_url(Url(timestamp=datetime.now(),
                              frequency=1,
                              url_type='C',
                              url='some url'))


def test_cluster_cascade_to_quotes(some_quotes):
    with session_scope() as session:
        session.query(Cluster).delete()
        assert session.query(Quote).count() == 0


def test_cluster_cascade_to_substitutions(some_substitutions):
    with session_scope() as session:
        session.query(Cluster).delete()
        assert session.query(Quote).count() == 0
        assert session.query(Substitution).count() == 0


def test_quote_cascade_to_substitutions(some_substitutions):
    with session_scope() as session:
        session.query(Quote).delete()
        assert session.query(Substitution).count() == 0


def test_substitution(some_substitutions):
    model1, model2 = some_substitutions
    with session_scope() as session:
        q10 = session.query(Quote).filter_by(sid=10).one()
        q11 = session.query(Quote).filter_by(sid=11).one()
        assert q10.substitutions_source.count() == 1
        assert q10.substitutions_destination.count() == 0
        assert q11.substitutions_source.count() == 0
        assert q11.substitutions_destination.count() == 3

        # Check relationships for a single substitution.
        s1 = q10.substitutions_source.first()
        assert q11.substitutions_destination\
            .order_by(Substitution.id).first() == s1
        assert s1.source == q10
        assert s1.destination == q11

        # Check linguistic variables.
        assert s1.tokens == ('would', 'had')
        assert s1.lemmas == ('would', 'have')
        assert s1.tags == ('MD', 'VHD')

        # We can filter substitutions by mining model.
        assert session.query(Substitution)\
            .filter(Substitution.model == model1).count() == 3
        assert session.query(Substitution)\
            .filter(Substitution.model == model2).count() == 2
        model3 = Model(Time.continuous, Source.majority,
                       Past.last_bin, Durl.all)
        assert session.query(Substitution)\
            .filter(Substitution.model == model3).count() == 0


def test_clone_cluster(some_urls):
    with session_scope() as session:
        cluster = session.query(Cluster).get(1)
        cloned = cluster.clone()
        assert cloned.id is None
        assert cloned.sid == cluster.sid
        assert cloned.filtered == cluster.filtered
        assert cloned.source == cluster.source
        assert cloned.quotes.all() == []

        cloned = cluster.clone(id=500, filtered=True, source='another')
        assert cloned.id == 500
        assert cloned.id != cluster.id
        assert cloned.sid == cluster.sid
        assert cloned.filtered is True
        assert cloned.filtered != cluster.filtered
        assert cloned.source == 'another'
        assert cloned.source != cluster.source
        assert cloned.quotes.all() == []


def test_clone_quote(some_urls):
    with session_scope() as session:
        quote = session.query(Quote).get(1)
        cloned = quote.clone()
        assert cloned.id is None
        assert cloned.cluster_id == quote.cluster_id
        assert cloned.sid == quote.sid
        assert cloned.filtered == quote.filtered
        assert cloned.string == quote.string
        for url in cloned.urls:
            assert url.quote == cloned
        # Urls are the same apart from parent quotes
        for url1, url2 in zip(quote.urls, cloned.urls):
            url1.quote = None
            url2.quote = None
        assert cloned.urls == quote.urls

        cloned = quote.clone(id=600, filtered=True,
                             cluster_id=125, string='hello')
        assert cloned.id == 600
        assert cloned.id != quote.id
        assert cloned.cluster_id == 125
        assert cloned.cluster_id != quote.cluster_id
        assert cloned.sid == quote.sid
        assert cloned.filtered is True
        assert cloned.filtered != quote.filtered
        assert cloned.string == 'hello'
        assert cloned.string != quote.string
        for url in cloned.urls:
            assert url.quote == cloned
        # Urls are the same apart from parent quotes
        for url1, url2 in zip(quote.urls, cloned.urls):
            url1.quote = None
            url2.quote = None
        assert cloned.urls == quote.urls
