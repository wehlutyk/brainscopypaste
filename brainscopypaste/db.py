"""Database models and related utilities.

This module defines the database structure underlying storage for the analysis.
This consists in models that get turned into PostgreSQL tables by `SQLAlchemy
<http://www.sqlalchemy.org/>`_, along with a few utility classes and exceptions
around them.

:class:`Cluster` and :class:`Quote` represent respectively an individual
cluster or quote from the MemeTracker data set. :class:`Url` represents a quote
occurrence, and those are stored as attributes to Quotes (as opposed to in
their own table). :class:`Substitution` represents an individual substitution
mined with a given substitution :class:`~.mine.Model`.

Each model (except Url, which doesn't have its own table) inherits the
:class:`BaseMixin`, which defines the table name, id, and provides a common
:meth:`BaseMixin.clone` method.

On top of that, models define a few computed properties (using the
:meth:`.utils.cache` decorator) which provide useful information that doesn't
need to be stored directly in the database (storing that in the database makes
subsequent access faster, but introduces more possibilities of inconsistent
data if updates don't align well). :class:`Cluster` and :class:`Substitution`
also inherit functionality from the :mod:`.mine` and :mod:`.filter` modules,
which you can inspect for more details.

Finally, this module defines :func:`save_by_copy`, useful for importing
clusters and quotes in bulk into the database.

"""


import re
from io import StringIO
import logging

import click
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, cast
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.types import DateTime, Enum, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY

from brainscopypaste.utils import cache, session_scope
from brainscopypaste.filter import ClusterFilterMixin
from brainscopypaste.mine import (SubstitutionValidatorMixin,
                                  ClusterMinerMixin, Model, Time, Source,
                                  Past, Durl)
from brainscopypaste.features import SubstitutionFeaturesMixin


logger = logging.getLogger(__name__)
Base = declarative_base()
Session = sessionmaker()


class BaseMixin:

    """Common mixin for all models defining table name, id, and `clone()`
    method."""

    @declared_attr
    def __tablename__(cls):
        """Compute the table name from the class name."""

        return cls.__name__.lower()

    #: Primary key for the table.
    id = Column(Integer, primary_key=True)

    def clone(self, **fields):
        """Clone a model instance, excluding the original `id` and optionally
        setting some fields to values provided as arguments.

        Give the fields to override as keyword arguments, their values will be
        set on the cloned instance. Any field that is not a known table column
        is ignored.

        """

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

    """Represent a MemeTracker cluster of quotes in the database.

    Attributes below are defined as class attributes or
    :class:`~.utils.cache`\ d methods, but they appear as instance attributes
    when you have an actual cluster instance. For instance, if `cluster` is a
    `Cluster` instance, `cluster.size` will give you that instance's
    :attr:`size`.

    """

    #: Id of the cluster that originated this instance, i.e. the id as it
    #: appears in the MemeTracker data set.
    sid = Column(Integer, nullable=False)
    #: Boolean indicating whether this cluster is part of the filtered (and
    #: kept) set of clusters or not.
    filtered = Column(Boolean, default=False, nullable=False)
    #: Source data set from which this cluster originated. Currently this is
    #: always `memetracker`.
    source = Column(String, nullable=False)
    #: List of :class:`Quote`\ s in this cluster (this is a dynamic
    #: relationship on which you can run queries).
    quotes = relationship('Quote', back_populates='cluster', lazy='dynamic',
                          cascade='all, delete-orphan', passive_deletes=True)

    #: Tuple of column names that are used by :meth:`format_copy`.
    format_copy_columns = ('id', 'sid', 'filtered', 'source')

    def format_copy(self):
        """Create a string representing the cluster in a
        :meth:`cursor.copy_from` call."""

        base = ('{cluster.id}\t{cluster.sid}\t{cluster.filtered}\t'
                '{cluster.source}')
        return base.format(cluster=self)

    @cache
    def size(self):
        """Number of quotes in the cluster."""

        return self.quotes.count()

    @cache
    def size_urls(self):
        """Number of urls of all the quotes in the cluster (i.e. not counting
        url frequencies)."""

        return sum(quote.size for quote in self.quotes.all())

    @cache
    def frequency(self):
        """Complete number of occurrences of all the quotes in the cluster
        (i.e. counting url frequencies)."""

        return sum(url.frequency for url in self.urls)

    @cache
    def urls(self):
        """Unordered list of :class:`Url`\ s of all the quotes in the
        cluster."""

        urls = []
        for quote in self.quotes.all():
            urls.extend(quote.urls)
        return sorted(urls, key=lambda url: url.timestamp)

    @cache
    def span(self):
        """Span of the cluster (as a :class:`~datetime.timedelta`), from first
        to last occurrence.

        Raises
        ------
        ValueError
            If no urls are defined on any quotes of the cluster.

        """

        if self.size_urls == 0:
            raise ValueError('No urls defined on any quotes of this cluster '
                             "yet, span doesn't make sense.")
        timestamps = []
        for quote in self.quotes.all():
            timestamps.extend(quote.url_timestamps)
        return abs(max(timestamps) - min(timestamps))


class ArrayOfEnum(ARRAY):

    """ARRAY of ENUMs column type, which is not directly supported by DBAPIs.

    This workaround is provided by `SQLAchemy's documentation
    <http://docs.sqlalchemy.org/en/rel_1_0/dialects/postgresql.html#using-enum-with-array>`_.

    """

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


#: :class:`sqlalchemy.types.Enum` of possible types of :class:`Url`\ s from
#: the MemeTracker data set.
url_type = Enum('B', 'M', name='url_type', metadata=Base.metadata)


class SealedException(Exception):
    """Exception raised when trying to edit a model on which
    :class:`~.utils.cache`\ d methods have already been accessed."""


class Quote(Base, BaseMixin):

    """Represent a MemeTracker quote in the database.

    Attributes below are defined as class attributes or
    :class:`~.utils.cache`\ d methods, but they appear as instance attributes
    when you have an actual quote instance. For instance, if `quote` is a
    `Quote` instance, `quote.size` will give you that instance's :attr:`size`.

    Note that children :class:`Url`\ s are stored directly inside this model
    through lists of url attributes, where a given url is defined by items at
    the same index in the various lists. This is an internal detail, and you
    should use the :attr:`urls` attribute to directly get a list of
    :class:`Url` objects.

    """

    #: Parent cluster id.
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'),
                        nullable=False)
    #: Parent :class:`Cluster`.
    cluster = relationship('Cluster', back_populates='quotes')
    #: Id of the quote that originated this instance, i.e. the id as it
    #: appears in the MemeTracker data set.
    sid = Column(Integer, nullable=False)
    #: Boolean indicating whether this quote is part of the filtered (and kept)
    #: set of quotes or not.
    filtered = Column(Boolean, default=False, nullable=False)
    #: Text of the quote.
    string = Column(String, nullable=False)
    #: List of :class:`~datetime.datetime`\ s representing the times at which
    #: children urls appear.
    url_timestamps = Column(ARRAY(DateTime), default=[], nullable=False)
    #: List of `int`\ s representing the frequencies of children urls (i.e. how
    #: many times the quote string appears at each url).
    url_frequencies = Column(ARRAY(Integer), default=[], nullable=False)
    #: List of :data:`url_type`\ s representing the types of the children urls.
    url_url_types = Column(ArrayOfEnum(url_type), default=[], nullable=False)
    #: List of `str`\ s representing the URIs of the children urls.
    url_urls = Column(ARRAY(String), default=[], nullable=False)
    #: List of :class:`Substitution`\ s for which this quote is the source
    #: (this is a dynamic relationship on which you can run queries).
    substitutions_source = relationship(
        'Substitution', back_populates='source', lazy='dynamic',
        foreign_keys='Substitution.source_id',
        cascade='all, delete-orphan', passive_deletes=True)
    #: List of :class:`Substitution`\ s for which this quote is the destination
    #: (this is a dynamic relationship on which you can run queries).
    substitutions_destination = relationship(
        'Substitution', back_populates='destination', lazy='dynamic',
        foreign_keys='Substitution.destination_id',
        cascade='all, delete-orphan', passive_deletes=True)

    #: Tuple of column names that are used by :meth:`format_copy`.
    format_copy_columns = ('id', 'cluster_id', 'sid', 'filtered', 'string',
                           'url_timestamps', 'url_frequencies',
                           'url_url_types', 'url_urls')

    def format_copy(self):
        """Create a string representing the quote and all its children urls in
        a :meth:`cursor.copy_from` call."""

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
        # (See http://www.postgresql.org/docs/9.5/static/arrays.html).
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
        """Number of urls in the quote."""

        if self.url_timestamps is None:
            return 0
        return len(self.url_timestamps)

    @cache
    def frequency(self):
        """Complete number of occurrences of the quote (i.e. counting url
        frequencies)."""

        if self.size == 0:
            return 0
        return sum(self.url_frequencies)

    @cache
    def span(self):
        """Span of the quote (as a :class:`~datetime.timedelta`), from first to
        last occurrence.

        Raises
        ------
        ValueError
            If no urls are defined on the quote.

        """

        if self.size == 0:
            raise ValueError('No urls defined on this quote yet, '
                             "span doesn't make sense.")
        timestamps = self.url_timestamps
        return abs(max(timestamps) - min(timestamps))

    @cache
    def tags(self):
        """List of TreeTagger POS tags of the tokens in the quote's :attr:`string`.

        Raises
        ------
        ValueError
            If the quote's :attr:`string` is `None`.

        """

        if self.string is None:
            raise ValueError('No string defined on this quote yet, '
                             "tags doesn't make sense.")
        from brainscopypaste import tagger
        return tagger.tags(self.string)

    @cache
    def tokens(self):
        """List of the tokens in the quote's :attr:`string`.

        Raises
        ------
        ValueError
            If the quote's :attr:`string` is `None`.

        """

        if self.string is None:
            raise ValueError('No string defined on this quote yet, '
                             "tokens doesn't make sense.")
        from brainscopypaste import tagger
        return tagger.tokens(self.string)

    @cache
    def lemmas(self):
        """List of the lemmas in the quote's :attr:`string`.

        Raises
        ------
        ValueError
            If the quote's :attr:`string` is `None`.

        """

        if self.string is None:
            raise ValueError('No string defined on this quote yet, '
                             "lemmas doesn't make sense.")
        from brainscopypaste import tagger
        return tagger.lemmas(self.string)

    @cache
    def urls(self):
        """Unordered list of :class:`Url`\ s of the quote."""

        if self.size == 0:
            return []
        return sorted([Url(timestamp, frequency, url_type, url, quote=self)
                       for (timestamp, frequency, url_type, url)
                       in zip(self.url_timestamps, self.url_frequencies,
                              self.url_url_types, self.url_urls)],
                      key=lambda url: url.timestamp)

    def add_url(self, url):
        """Add a :class:`Url` to the quote.

        The change is not automatically saved. If you want to persist this to
        the database, you should do it inside a session and commit afterwards
        (e.g. using :func:`~.utils.session_scope`).

        Parameters
        ----------
        url : :class:`Url`
            The url to add to the quote.

        Raises
        ------
        SealedException
            If the :attr:`urls` attribute has already been accessed; since that
            attribute is :class:`~.utils.cache`\ d, adding a url to the quote
            would invalidate the value.

        """

        if 'urls' in self.__dict__:
            raise SealedException('self.urls has already been accessed, '
                                  'cannot add more urls')
        self.url_timestamps = (self.url_timestamps or []) + [url.timestamp]
        self.url_frequencies = (self.url_frequencies or []) + [url.frequency]
        self.url_url_types = (self.url_url_types or []) + [url.url_type]
        self.url_urls = (self.url_urls or []) + [url.url]

    def add_urls(self, urls):
        """Add a list of :class:`Url`\ s to the quote.

        As for :meth:`add_url`, the changes are not automatically saved. If you
        want to persist this to the database, you should do it inside a session
        and commit afterwards (e.g. using :func:`~.utils.session_scope`).

        Parameters
        ----------
        urls : list of :class:`Url`\ s
            The urls to add to the quote.

        Raises
        ------
        SealedException
            If the :attr:`urls` attribute has already been accessed; since that
            attribute is :class:`~.utils.cache`\ d, adding urls to the quote
            would invalidate the value.

        """

        for url in urls:
            self.add_url(url)


class Url:

    """Represent a MemeTracker url in a :class:`Quote` in the database.

    The url :attr:`occurrence` is defined below as a :class:`~.utils.cache`\ d
    method, but it appears as an instance attribute when you have an actual url
    instance. For instance, if `url` is a `Url` instance, `url.occurrence` will
    give you that url's :attr:`occurrence`.

    Note that :class:`Url`\ s are stored directly inside :class:`Quote`
    instances, and don't have a dedicated database table.

    Attributes
    ----------
    quote : :class:`Quote`
        Parent quote.
    timestamp : :class:`~datetime.datetime`
        Time at which the url occurred.
    frequency : int
        Number of times the quote string appears at this url.
    url_type : :data:`url_type`
        Type of this url.
    url : str
        URI of this url.

    """

    def __init__(self, timestamp, frequency, url_type, url, quote=None):
        self.quote = quote
        self.timestamp = timestamp
        self.frequency = frequency
        self.url_type = url_type
        self.url = url

    def __key(self):
        """Unique identifier for this url, used to compute e.g. equality."""

        return (self.quote, self.timestamp, self.frequency,
                self.url_type, self.url)

    def __eq__(self, other):
        """Determine if two instances represent the same url (underlies e.g.
        ``url1 == url2``)"""

        return self.__key() == other.__key()

    def __hash__(self):
        """Hash for this url (makes this class hashable, so usable e.g. as dict
        keys)."""

        return hash(self.__key())

    @cache
    def occurrence(self):
        """Index of the url in the list of urls of the parent :class:`Quote`.

        Raises
        ------
        ValueError
            If the url's `quote` attribute is `None`.

        """

        if self.quote is None:
            raise ValueError('No quote defined on this Url')
        return self.quote.urls.index(self)


class ModelType(TypeDecorator):

    """Database type representing a substitution :class:`~.mine.Model`, used in
    the definition of :class:`Substitution`."""

    impl = String

    def process_bind_param(self, value, dialect):
        """Convert a :class:`~.mine.Model` to its database representation."""

        return str(value)

    def process_result_value(self, value, dialect):
        """Create a :class:`~.mine.Model` instance from its database
        representation."""

        return eval(value, globals(),
                    {'Model': Model, 'Source': Source, 'Time': Time,
                     'Durl': Durl, 'Past': Past})


class Substitution(Base, BaseMixin, SubstitutionValidatorMixin,
                   SubstitutionFeaturesMixin):

    """Represent a substitution in the database from one :class:`Quote` to another.

    A substitution is the replacement of a word from one quote (or a substring
    of that quote) in another quote. It is defined by a :attr:`source quote
    <source>`, an :attr:`occurrence` of a :attr:`destination quote
    <destination>`, the :attr:`position of a substring <start>` in the source
    quote string, the :attr:`position of the replaced word <position>` in that
    substring, and the :attr:`substitution model <model>` that detected the
    substitution in the data set.

    Attributes below are defined as class attributes or
    :class:`~.utils.cache`\ d methods, but they appear as instance attributes
    when you have an actual substitution instance. For instance, if
    `substitution` is a `Substitution` instance, `substitution.tags` will give
    you that instance's :attr:`tags`.

    """

    #: Id of the source quote for the substitution.
    source_id = Column(Integer,
                       ForeignKey('quote.id', ondelete='CASCADE'),
                       nullable=False)
    #: Source :class:`Quote` for the substitution.
    source = relationship('Quote', back_populates='substitutions_source',
                          foreign_keys='Substitution.source_id')
    #: Id of the destination quote for the substitution.
    destination_id = Column(Integer,
                            ForeignKey('quote.id', ondelete='CASCADE'),
                            nullable=False)
    #: Destination :class:`Quote` for the substitution.
    destination = relationship('Quote',
                               back_populates='substitutions_destination',
                               foreign_keys='Substitution.destination_id')

    #: Index of the destination :class:`Url` in the destination quote.
    occurrence = Column(Integer, nullable=False)
    #: Index of the beginning of the substring in the source quote.
    start = Column(Integer, nullable=False)
    #: Position of the replaced word *in the substring of the source quote*
    #: (which is also the position in the destination quote).
    position = Column(Integer, nullable=False)
    #: Substitution detection :class:`~.mine.Model` that detected this
    #: substitution.
    model = Column(ModelType, nullable=False)

    @cache
    def tags(self):
        """Tuple of TreeTagger POS tags of the replaced and replacing words."""

        return (self.source.tags[self.start + self.position],
                self.destination.tags[self.position])

    @cache
    def tokens(self):
        """Tuple of the replaced and replacing words (the tokens here are the
        exact replaced and replacing words)."""

        return (self.source.tokens[self.start + self.position],
                self.destination.tokens[self.position])

    @cache
    def lemmas(self):
        """Tuple of lemmas of the replaced and replacing words."""

        return (self.source.lemmas[self.start + self.position],
                self.destination.lemmas[self.position])


def _copy(string, table, columns):
    """Execute a PostgreSQL COPY command.

    COPY is one of the fastest methods to import data in bulk into PostgreSQL.
    This function executes this operation through the raw psycopg2
    :class:`cursor` object.

    Parameters
    ----------
    string : file-like object
        Contents of the data to import into the database, formatted for the
        COPY command (see `PostgreSQL's documentation
        <https://www.postgresql.org/docs/9.5/static/sql-copy.html>`_ for more
        details). Can be an :class:`io.StringIO` if you don't want to use a
        real file in the filesystem.
    table : str
        Name of the table into which the data is imported.
    columns : list of str
        List of the column names encoded in the `string` parameter. When
        `string` is produced using :meth:`Quote.format_copy` or
        :meth:`Cluster.format_copy` you can use the corresponding
        :attr:`Quote.format_copy_columns` or
        :attr:`Cluster.format_copy_columns` for this parameter.

    See Also
    --------
    save_by_copy, Quote.format_copy, Cluster.format_copy

    """

    string.seek(0)
    with session_scope() as session:
        cursor = session.connection().connection.cursor()
        cursor.copy_from(string, table, columns=columns)


def save_by_copy(clusters, quotes):
    """Import a list of clusters and a list of quotes into the database.

    This function uses PostgreSQL's COPY command to bulk import clusters and
    quotes, and prints its progress to stdout.

    Parameters
    ----------
    clusters : list of :class:`Cluster`\ s
        List of clusters to import in the database.
    quotes : list of :class:`Quote`\ s
        List of quotes to import in the database. Any clusters they reference
        should be in the `clusters` parameters.

    See Also
    --------
    .load.MemeTrackerParser.parse

    """

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
