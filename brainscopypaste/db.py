import re
from datetime import timedelta
from io import StringIO
import logging

import click
from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey,
                        PickleType, cast)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.types import DateTime, Enum
from sqlalchemy.dialects.postgresql import ARRAY

from brainscopypaste.utils import cache
from brainscopypaste.filter import ClusterFilterMixin
from brainscopypaste.mine import SubstitutionValidatorMixin, ClusterMinerMixin


logger = logging.getLogger(__name__)
Base = declarative_base()
Session = sessionmaker()


class BaseMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

    def clone(self, **fields):
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


class Cluster(Base, BaseMixin, ClusterFilterMixin, ClusterMinerMixin):

    sid = Column(Integer, nullable=False)
    filtered = Column(Boolean, default=False, nullable=False)
    source = Column(String, nullable=False)
    quotes = relationship('Quote', back_populates='cluster', lazy='dynamic',
                          cascade='all, delete-orphan', passive_deletes=True)

    format_copy_columns = ('id', 'sid', 'filtered', 'source')

    def format_copy(self):
        base = ('{cluster.id}\t{cluster.sid}\t{cluster.filtered}\t'
                '{cluster.source}')
        return base.format(cluster=self)

    @cache
    def size(self):
        return self.quotes.count()

    @cache
    def size_urls(self):
        return sum(quote.size for quote in self.quotes.all())

    @cache
    def frequency(self):
        return sum(url.frequency for url in self.urls)

    @cache
    def urls(self):
        urls = []
        for quote in self.quotes.all():
            urls.extend(quote.urls)
        return sorted(urls, key=lambda url: url.timestamp)

    @cache
    def span(self):
        if self.size_urls == 0:
            return timedelta(0)
        timestamps = []
        for quote in self.quotes.all():
            timestamps.extend(quote.url_timestamps)
        return abs(max(timestamps) - min(timestamps))


class ArrayOfEnum(ARRAY):

    def bind_expression(self, bindvalue):
        return cast(bindvalue, self)

    def result_processor(self, dialect, coltype):
        super_rp = super(ArrayOfEnum, self).result_processor(
            dialect, coltype)

        def handle_raw_string(value):
            inner = re.match(r"^{(.*)}$", value).group(1)
            return inner.split(",") if inner else []

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))
        return process


url_type = Enum('B', 'M', name='url_type', metadata=Base.metadata)


class SealedException(Exception):
    pass


class Quote(Base, BaseMixin):

    # TODO: test that deleting clusters deletes this.
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'),
                        nullable=False)
    cluster = relationship('Cluster', back_populates='quotes')
    sid = Column(Integer, nullable=False)
    filtered = Column(Boolean, default=False, nullable=False)
    string = Column(String, nullable=False)
    url_timestamps = Column(ARRAY(DateTime), default=[], nullable=False)
    url_frequencies = Column(ARRAY(Integer), default=[], nullable=False)
    url_url_types = Column(ArrayOfEnum(url_type), default=[], nullable=False)
    url_urls = Column(ARRAY(String), default=[], nullable=False)
    substitutions_source = relationship(
        'Substitution', back_populates='source', lazy='dynamic',
        foreign_keys='Substitution.source_id',
        cascade='all, delete-orphan', passive_deletes=True)
    substitutions_destination = relationship(
        'Substitution', back_populates='destination', lazy='dynamic',
        foreign_keys='Substitution.destination_id',
        cascade='all, delete-orphan', passive_deletes=True)

    format_copy_columns = ('id', 'cluster_id', 'sid', 'filtered', 'string',
                           'url_timestamps', 'url_frequencies',
                           'url_url_types', 'url_urls')

    def format_copy(self):
        base = '{quote.id}\t{quote.cluster_id}\t{quote.sid}\t{quote.filtered}'
        parts = [base.format(quote=self)]
        # Backslashes must be escaped otherwise PostgreSQL interprets them
        # in its own way (see
        # http://www.postgresql.org/docs/current/interactive/sql-copy.html).
        parts.append(self.string.replace('\\', '\\\\'))
        timestamps = [url.timestamp for url in self.urls]
        frequencies = [url.frequency for url in self.urls]
        url_types = [url.url_type for url in self.urls]
        parts.append('{' +
                     ', '.join(map('{}'.format, timestamps)) +
                     '}')
        parts.append('{' +
                     ', '.join(map('{}'.format, frequencies)) +
                     '}')
        parts.append('{' +
                     ', '.join(map('{}'.format, url_types)) +
                     '}')
        # Two levels of escaping backslashes and double quotes too here.
        # (See http://www.postgresql.org/docs/9.4/static/arrays.html).
        urls = [url.url.replace('\\', '\\\\').replace('"', '\\"')
                for url in self.urls]
        parts.append(
            "{" +
            ', '.join(map('"{}"'.format, urls)).replace('\\', '\\\\') +
            "}"
        )
        return '\t'.join(parts)

    @cache
    def size(self):
        if self.url_timestamps is None:
            return 0
        return len(self.url_timestamps)

    @cache
    def frequency(self):
        return sum(self.url_frequencies)

    @cache
    def span(self):
        if self.size == 0:
            return timedelta(0)
        timestamps = self.url_timestamps
        return abs(max(timestamps) - min(timestamps))

    @cache
    def tags(self):
        from brainscopypaste import tagger
        return tagger.tags(self.string)

    @cache
    def tokens(self):
        from brainscopypaste import tagger
        return tagger.tokens(self.string)

    @cache
    def lemmas(self):
        from brainscopypaste import tagger
        return tagger.lemmas(self.string)

    @cache
    def urls(self):
        if self.size == 0:
            return []
        return sorted([Url(timestamp, frequency, url_type, url, quote=self)
                       for (timestamp, frequency, url_type, url)
                       in zip(self.url_timestamps, self.url_frequencies,
                              self.url_url_types, self.url_urls)],
                      key=lambda url: url.timestamp)

    def add_url(self, url):
        if 'urls' in self.__dict__:
            raise SealedException('self.urls has already been accessed, '
                                  'cannot add more urls')
        self.url_timestamps = (self.url_timestamps or []) + [url.timestamp]
        self.url_frequencies = (self.url_frequencies or []) + [url.frequency]
        self.url_url_types = (self.url_url_types or []) + [url.url_type]
        self.url_urls = (self.url_urls or []) + [url.url]

    def add_urls(self, urls):
        for url in urls:
            self.add_url(url)


class Url:

    def __init__(self, timestamp, frequency, url_type, url, quote=None):
        self.quote = quote
        self.timestamp = timestamp
        self.frequency = frequency
        self.url_type = url_type
        self.url = url

    def __key(self):
        return (self.quote, self.timestamp, self.frequency,
                self.url_type, self.url)

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    @cache
    def occurrence(self):
        if self.quote is None:
            raise ValueError('No quote defined on this Url')
        return self.quote.urls.index(self)


class Substitution(Base, BaseMixin, SubstitutionValidatorMixin):

    # TODO: test that deleting quotes, or clusters deletes this.
    source_id = Column(Integer,
                       ForeignKey('quote.id', ondelete='CASCADE'),
                       nullable=False)
    source = relationship('Quote', back_populates='substitutions_source',
                          foreign_keys='Substitution.source_id')
    destination_id = Column(Integer,
                            ForeignKey('quote.id', ondelete='CASCADE'),
                            nullable=False)
    destination = relationship('Quote',
                               back_populates='substitutions_destination',
                               foreign_keys='Substitution.destination_id')

    # Index of the url in the destination quote.
    occurrence = Column(Integer, nullable=False)
    # Index of the beginning of the substring in the source quote.
    start = Column(Integer, nullable=False)
    # Position of the substitution *in the substring of the source quote*
    # (which is also the position in the destination quote).
    position = Column(Integer, nullable=False)
    # Detection model that created this substitution.
    model = Column(PickleType, nullable=False)

    @cache
    def tags(self):
        return (self.source.tags[self.start + self.position],
                self.destination.tags[self.position])

    @cache
    def tokens(self):
        return (self.source.tokens[self.start + self.position],
                self.destination.tokens[self.position])

    @cache
    def lemmas(self):
        return (self.source.lemmas[self.start + self.position],
                self.destination.lemmas[self.position])


def _copy(string, table, columns):
    from brainscopypaste.utils import session_scope

    string.seek(0)
    with session_scope() as session:
        cursor = session.connection().connection.cursor()
        cursor.copy_from(string, table, columns=columns)


def save_by_copy(clusters, quotes):
    # Order the objects inserted so the engine bulks them together.
    logger.debug("Saving %s clusters with 'copy_from'", len(clusters))
    click.echo('Saving clusters... ', nl=False)
    objects = StringIO()
    objects.writelines([cluster.format_copy() + '\n' for cluster in clusters])
    _copy(objects, Cluster.__tablename__, Cluster.format_copy_columns)
    objects.close()
    click.secho('OK', fg='green', bold=True)

    logger.debug("Saving %s quotes with 'copy_from'", len(quotes))
    click.echo('Saving quotes... ', nl=False)
    objects = StringIO()
    objects.writelines([quote.format_copy() + '\n' for quote in quotes])
    _copy(objects, Quote.__tablename__, Quote.format_copy_columns)
    objects.close()
    click.secho('OK', fg='green', bold=True)
