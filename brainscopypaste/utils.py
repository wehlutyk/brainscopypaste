"""Miscellaneous utilities.

"""


import logging
import pickle
from contextlib import contextmanager
from itertools import zip_longest
import os

import numpy as np
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from sqlalchemy import create_engine
from decorator import decorate


logger = logging.getLogger(__name__)


class Namespace:

    """Convert a dict to a namespace by creating a class out of it.

    Parameters
    ----------
    init_dict : dict
        The dict you wish to turn into a namespace.

    """

    def __init__(self, init_dict):
        self.__dict__.update(init_dict)


def grouper(iterable, n, fillvalue=None):
    """Iterate over `n`-wide slices of `iterable`, filling the
    last slice with `fillvalue`.

    See :func:`grouper_adaptive` for a version of this that doesn't fill the
    last slice.

    """

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def grouper_adaptive(iterable, n):
    """Iterate over `n`-wide slices of `iterable`, ending the last slice once
    `iterable` is empty.

    See :func:`grouper_adaptive` for a version of this that fills the last
    slice with a value of your choosing.

    """

    it = iter(iterable)
    keepgoing = True

    def block():
        nonlocal keepgoing
        for i in range(n):
            try:
                yield next(it)
            except StopIteration:
                keepgoing = False

    while keepgoing:
        yield block()


class cache:
    """Compute an attribute's value and cache it in the instance.

    This is meant to be used as a decorator on class methods, to turn them into
    cached computed attributes: the value is computed the first time you access
    the attribute, and this decorator then replaces the method with the
    computed value. Any subsequent access gives you the cached value
    immediately.

    Taken from the `Python Cookbook (Denis Otkidach)
    <http://stackoverflow.com/users/168352/denis-otkidach>`_.

    """

    def __init__(self, method, name=None):
        # Record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        # self: <__main__.cache object at 0xb781340c>
        # inst: <__main__.Foo object at 0xb781348c>
        # cls: <class '__main__.Foo'>
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self

        # Compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't
        # get called again
        setattr(inst, self.name, result)
        return result


def _memoize(func, *args, **kwargs):
    # frozenset is used to ensure hashability
    if kwargs:
        key = args, frozenset(kwargs.items())
    else:
        key = args
    # Attribute added by memoized
    cache = func.cache
    if key not in cache:
        cache[key] = func(*args, **kwargs)
    return cache[key]


def memoized(f):
    """Decorate a function to cache its return value the first time it is
    called.

    If called later with the same arguments, the cached value is returned
    (not reevaluated).

    """

    f.cache = {}

    def drop_cache():
        logger.debug('Dropping cache for %s', f)
        f.cache = {}

    f.drop_cache = drop_cache
    return decorate(f, _memoize)


def mpl_palette(n_colors, variation='Set2'):  # or variation='colorblind'
    """Get any seaborn palette as a usable matplotlib colormap."""

    import seaborn as sb
    palette = sb.color_palette(variation, n_colors, desat=0.8)
    return (sb.blend_palette(palette, n_colors=n_colors, as_cmap=True),
            sb.blend_palette(palette, n_colors=n_colors))


@contextmanager
def session_scope():
    """Provide an SQLAlchemy transactional scope around a series of
    operations.

    Wrap your SQLAlchemy operations (queries, insertions, modifications, etc.)
    in a ``with session_scope() as session`` block to deal with sessions
    easily.  Changes are committed when the block finishes. If an exception
    occurrs in the block, the session is rolled back and the exception
    propagated.

    """

    from brainscopypaste.db import Session
    session = Session()
    logger.debug('Opened session %s', session)
    try:
        yield session
        logger.debug('Committing session %s', session)
        session.commit()
    except:
        logger.debug('Rolling back session %s', session)
        session.rollback()
        raise
    finally:
        logger.debug('Closing session %s', session)
        session.close()


def mkdirp(folder):
    """Create `folder` if it doesn't exist."""

    if not os.path.exists(folder):
        logger.debug("Creating folder '%s'", folder)
        os.makedirs(folder)


def iter_parent_dirs(rel_dir):
    """Iterate through parent directories of current working directory,
    appending `rel_dir` to those successive directories."""

    d = os.path.abspath('.')
    pd = None
    while pd != d:
        yield os.path.join(d, rel_dir)
        pd = d
        d = os.path.split(d)[0]


def find_parent_rel_dir(rel_dir):
    """Find a relative directory in parent directories.

    Searches for directory `rel_dir` in all parent directories of the current
    directory.

    Parameters
    ----------
    rel_dir : string
        The relative directory to search for.

    Returns
    -------
    d : string
        Full path to the first found directory.

    Raises
    ------
    NotFoundError
        If no relative directory is found in the parent directories.

    """

    for d in iter_parent_dirs(rel_dir):
        if os.path.exists(d) and os.path.isdir(d):
            return d

    raise NotFoundError('No relative directory found in parent directories')


class NotFoundError(Exception):
    """Signal a file or directory can't be found."""


@memoized
def langdetect(sentence):
    """Detect the language of `sentence`."""

    try:
        return detect(sentence)
    except LangDetectException:
        return None


def execute_raw(engine, statement):
    """Execute the raw SQL statement `statement` on SQLAlchemy engine `engine`.

    Useful to run ANALYZE or VACUUM operations on the database.

    Parameters
    ----------
    engine : :class:`sqlalchemy.engine.Engine`
        The engine to run `statement` on.
    statement : str
        A valid SQL statement for `engine`.

    """

    logger.debug("Raw execution of SQL '%s'", statement)

    connection = engine.connect()
    raw_connection = connection.connection
    old_isolation_level = raw_connection.isolation_level
    raw_connection.set_isolation_level(0)
    with raw_connection.cursor() as cursor:
        cursor.execute(statement)
    raw_connection.set_isolation_level(old_isolation_level)
    connection.close()


@memoized
def is_same_ending_us_uk_spelling(w1, w2):
    """Test if `w1` and `w2` differ by only the last two letters inverted,
    as in `center`/`centre` (words must be at least 4 letters)."""

    if len(w1) < 4 or len(w2) < 4:
        # Words too short
        return False

    if w1[:-2] != w2[:-2]:
        # There's a change before the last two letters
        return False

    if w1[:-3:-1] == w2[-2:]:
        # The last two letters are inverted
        return True

    return False


@memoized
def is_int(s):
    """Test if `s` is a string that represents an integer; returns `True` if
    so, `False` in any other case."""

    if not isinstance(s, str) or isinstance(s, bytes):
        return False
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


@memoized
def levenshtein(s1, s2):
    """Compute the levenshtein distance between strings or lists `s1` and
    `s2`."""

    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if not s2:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # previous_row and current_row are one character longer than s2,
            # hence the 'j + 1'
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


@memoized
def hamming(s1, s2):
    """Compute the hamming distance between strings or lists `s1` and `s2`."""

    if len(s1) != len(s2):
        raise ValueError('Strings must be the same length.')
    else:
        return np.sum(c1 != c2 for c1, c2 in zip(s1, s2))


@memoized
def sublists(s, l):
    """Get all sublists of `s` of length `l`."""

    if l == 0:
        return ()
    if l > len(s):
        raise ValueError('Sublists must be shorter or as long as source.')
    return tuple(s[i:i + l] for i in range(len(s) - l + 1))


@memoized
def subhamming(s1, s2):
    """Compute the minimum hamming distance between `s2` and all sublists of
    `s1` as long as `s2`, returning `(distance, sublist start in s1)`."""

    l1 = len(s1)
    l2 = len(s2)

    if l2 == 0:
        return l1, 0

    if l1 < l2:
        raise ValueError('The second string must be shorter or '
                         'as long as the first one.')
    if l1 == l2:
        return hamming(s1, s2), 0

    distances = np.zeros(l1 - l2 + 1)

    for i, subs in enumerate(sublists(s1, l2)):
        distances[i] = hamming(subs, s2)

    amin = np.argmin(distances)
    return int(distances[amin]), amin


class Stopwords:

    """Detect if a word is a stopword.

    Prefer using this module's :data:`stopwords` instance of this class for
    stopword-checking.

    """

    def __init__(self):
        self._loaded = False

    def _load(self):
        """Read and load the underlying stopwords file."""

        logger.debug('Loading stopwords')

        from brainscopypaste.conf import settings
        stopwords = set([])
        with open(settings.STOPWORDS) as f:
            for l in f:
                stopwords.add(l.strip().lower())

        self._stopwords = stopwords
        self._loaded = True

    def __contains__(self, word):
        """Test if `word` is a stopword or not."""

        if not self._loaded:
            self._load()
        return word in self._stopwords


#: Instance of :class:`Stopwords` to be used for stopword-testing.
stopwords = Stopwords()


@memoized
def unpickle(filename):
    """Load a pickle file at path `filename`.

    This function is :func:`memoized` so a file is only loaded the first time.

    """

    with open(filename, 'rb') as file:
        return pickle.load(file)


def init_db(echo_sql=False):
    """Connect to the database and bind :mod:`.db`'s `Session` object to it.

    Uses the :data:`~.settings.DB_USER` and :data:`~.settings.DB_PASSWORD`
    credentials to connect to PostgreSQL database :data:`~.settings.DB_NAME`.
    It binds the `Session` object in :mod:`.db` to this engine, and returns the
    engine object. Note that once this is done, you can directly use
    :func:`session_scope` since it uses the right `Session` object.

    Parameters
    ----------
    echo_sql : bool, optional
        If `True`, print to stdout all SQL commands sent to the engine;
        defaults to `False`.

    Returns
    -------
    :class:`sqlalchemy.engine.Engine`
        The engine connected to the database.

    """

    from brainscopypaste.db import Base, Session
    from brainscopypaste.conf import settings
    logger.info('Initializing database connection')

    engine = create_engine(
        'postgresql+psycopg2://{user}:{pw}@localhost:5432/{db}'
        .format(user=settings.DB_USER, pw=settings.DB_PASSWORD,
                db=settings.DB_NAME),
        client_encoding='utf8', echo=echo_sql)
    Session.configure(bind=engine)

    logger.info('Database connected')
    logger.debug('Checking tables to create')

    Base.metadata.create_all(engine)
    return engine
