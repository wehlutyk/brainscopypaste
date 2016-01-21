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

    id = Column(Integer, primary_key=True, nullable=False)


class Cluster(Base, BaseMixin):

    source = Column(String, nullable=False)
    quotes = relationship('Quote', back_populates='cluster')

    @property
    def size(self):
        # TODO: cache
        # TODO: check at load
        return len(self.quotes)

    @property
    def frequency(self):
        # TODO: cache
        # TODO: check at load
        return sum(quote.frequency for quote in self.quotes)


class Quote(Base, BaseMixin):

    cluster_id = Column(Integer, ForeignKey('cluster.id'), nullable=False)
    cluster = relationship('Cluster', back_populates='quotes')
    string = Column(String, nullable=False)
    urls = relationship('Url', back_populates='quote')

    @property
    def size(self):
        # TODO: cache
        # TODO: check at load
        return len(self.urls)

    @property
    def frequency(self):
        # TODO: cache
        # TODO: check at load
        return sum(url.frequency for url in self.urls)


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
