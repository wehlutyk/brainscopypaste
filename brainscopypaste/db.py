from datetime import timedelta

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.types import DateTime, Enum


Base = declarative_base()
Session = sessionmaker()


class BaseMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)


class Cluster(Base, BaseMixin):

    sid = Column(Integer, nullable=False)
    source = Column(String, nullable=False)
    quotes = relationship('Quote', back_populates='cluster')

    @property
    def size(self):
        # TODO: cache
        return len(self.quotes)

    @property
    def size_urls(self):
        # TODO: cache
        return self.urls.count()

    @property
    def frequency(self):
        # TODO: cache
        return sum(quote.frequency for quote in self.quotes)

    @property
    def urls(self):
        # TODO: cache
        from brainscopypaste.utils import session_scope
        with session_scope() as session:
            quote_ids = [quote.id for quote in self.quotes]
            return session.query(Url).filter(Url.quote_id.in_(quote_ids))

    @property
    def span(self):
        # TODO: cache
        if self.size_urls == 0:
            return timedelta(0)
        return abs(self.urls.order_by('timestamp desc').first().timestamp -
                   self.urls.order_by('timestamp').first().timestamp)


class Quote(Base, BaseMixin):

    cluster_id = Column(Integer, ForeignKey('cluster.id'), nullable=False)
    cluster = relationship('Cluster', back_populates='quotes')
    sid = Column(Integer, nullable=False)
    string = Column(String, nullable=False)
    urls = relationship('Url', back_populates='quote', lazy='dynamic')

    @property
    def size(self):
        # TODO: cache
        return self.urls.count()

    @property
    def frequency(self):
        # TODO: cache
        return sum(url.frequency for url in self.urls)

    @property
    def span(self):
        # TODO: cache
        if self.size == 0:
            return timedelta(0)
        return abs(self.urls.order_by('timestamp desc').first().timestamp -
                   self.urls.order_by('timestamp').first().timestamp)


class Url(Base, BaseMixin):

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=False)
    quote = relationship('Quote', back_populates='urls')
    timestamp = Column(DateTime, nullable=False)
    frequency = Column(Integer, nullable=False)
    url_type = Column(Enum('B', 'M', name='url_type'), nullable=False)
    url = Column(String, nullable=False)

    @property
    def cluster(self):
        # TODO: cache
        return self.quote.cluster
