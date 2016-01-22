from datetime import timedelta

from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey, desc,
                        inspect, func)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.types import DateTime, Enum

from brainscopypaste.utils import cache
from brainscopypaste.filter import FilterMixin


Base = declarative_base()
Session = sessionmaker()


class BaseMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

    def clone(self, **fields):
        # TODO: test
        columns = self.__mapper__.columns.keys()
        columns.remove('id')
        for field in fields.keys():
            try:
                columns.remove(field)
            except ValueError:
                pass

        init = {}
        for column in columns:
            init[column] = getattr(self, column)

        for arg, value in fields.items():
            init[arg] = value

        return self.__class__(**init)


class Cluster(Base, BaseMixin, FilterMixin):

    sid = Column(Integer, nullable=False)
    filtered = Column(Boolean, default=False, nullable=False)
    source = Column(String, nullable=False)
    quotes = relationship('Quote', back_populates='cluster', lazy='dynamic')

    @cache
    def size(self):
        return self.quotes.count()

    @cache
    def size_urls(self):
        return self.urls.count()

    @cache
    def frequency(self):
        return sum(quote.frequency for quote in self.quotes)

    @cache
    def urls(self):
        session = inspect(self).session
        quote_ids = [quote.id for quote in self.quotes]
        # Not that the line above could work while not in a session,
        # if the quotes were eagerly loaded, so we do need to check
        # that the session we obtained is not None.
        if session is None:
            raise ValueError(("Instance {} is not bound to a Session; "
                              "cannot load attributes.").format(self))
        return session.query(Url).filter(Url.quote_id.in_(quote_ids))

    @cache
    def span(self):
        if self.size_urls == 0:
            return timedelta(0)
        return abs(self.urls.order_by(desc(Url.timestamp)).first().timestamp -
                   self.urls.order_by(Url.timestamp).first().timestamp)


class Quote(Base, BaseMixin):

    cluster_id = Column(Integer, ForeignKey('cluster.id'), nullable=False)
    cluster = relationship('Cluster', back_populates='quotes')
    sid = Column(Integer, nullable=False)
    filtered = Column(Boolean, default=False, nullable=False)
    string = Column(String, nullable=False)
    urls = relationship('Url', back_populates='quote', lazy='dynamic')

    @cache
    def size(self):
        return self.urls.count()

    @cache
    def frequency(self):
        if self.size == 0:
            return 0
        return self.urls.with_entities(func.sum(Url.frequency)).scalar()

    @cache
    def span(self):
        if self.size == 0:
            return timedelta(0)
        return abs(self.urls.with_entities(func.max(Url.timestamp)).scalar() -
                   self.urls.with_entities(func.min(Url.timestamp)).scalar())

    @cache
    def tokens(self):
        from brainscopypaste import tagger
        return tagger.tokens(self.string)


class Url(Base, BaseMixin):

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=False)
    quote = relationship('Quote', back_populates='urls')
    filtered = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    frequency = Column(Integer, nullable=False)
    url_type = Column(Enum('B', 'M', name='url_type'), nullable=False)
    url = Column(String, nullable=False)

    @cache
    def cluster(self):
        return self.quote.cluster
