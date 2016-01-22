import collections
from contextlib import contextmanager
import functools
from itertools import zip_longest
import os

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def grouper(iterable, n, fillvalue=None):
    """Iterate over `n`-wide slices of `iterable`, filling the
    last slice with `fillvalue`."""

    # TODO: test
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def grouper_adaptive(iterable, n):
    # TODO: test
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
    """Computes attribute value and caches it in the instance.

    Python Cookbook (Denis Otkidach)
    http://stackoverflow.com/users/168352/denis-otkidach This decorator allows
    you to create a property which can be computed once and accessed many
    times. Sort of like memoization.

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


class memoized(object):
    """Decorate a function to cache its return value each time it is called.

    If called later with the same arguments, the cached value is returned
    (not reevaluated).

    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        try:
            key = (args, frozenset(kwargs.items()))
        except TypeError:
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args, **kwargs)

        if not isinstance(args, collections.Hashable):
            # again uncacheable
            return self.func(*args, **kwargs)

        if key in self.cache:
            return self.cache[key]
        else:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


def mpl_palette(n_colors, variation='Set2'):  # or variation='colorblind'
    """Get any seaborn palette as a usable matplotlib colormap."""

    import seaborn as sb
    palette = sb.color_palette(variation, n_colors, desat=0.8)
    return (sb.blend_palette(palette, n_colors=n_colors, as_cmap=True),
            sb.blend_palette(palette, n_colors=n_colors))


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    from brainscopypaste.db import Session
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def mkdirp(folder):
    """Create `folder` if it doesn't exist."""
    if not os.path.exists(folder):
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

    See Also
    --------
    iter_upper_dirs, NotFoundError

    """

    for d in iter_parent_dirs(rel_dir):
        if os.path.exists(d) and os.path.isdir(d):
            return d

    raise NotFoundError('No relative directory found in parent directories')


class NotFoundError(Exception):
    """Signal a file or directory can't be found."""


@memoized
def langdetect(sentence):
    try:
        return detect(sentence)
    except LangDetectException:
        return None
