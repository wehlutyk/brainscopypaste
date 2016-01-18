import collections
from contextlib import contextmanager
import functools
from itertools import zip_longest

from db import Session


def grouper(iterable, n, fillvalue=None):
    """Iterate over `n`-wide slices of `iterable`, filling the
    last slice with `fillvalue`."""

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


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
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
