#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generic utility methods.

These methods are helpers used to manipulate lists, dicts, and classes.

"""


from __future__ import division

import re
import os

import numpy as np


def is_twelfth_int(values):
    """Is `values` made of twefths of integers or not."""

    return (map(int, 12 * values) == 12 * values).mean() > 0.99


def memoize(func):
    """Wrap `func` in a caching function."""

    cache = {}

    def inner(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return inner


def inv_dict(d):
    """Create the dict of `v, k` mappings where `d[k] = v`."""

    inv_d = {}
    for k, v in d.iteritems():
        inv_d[v] = k
    return inv_d


def indices_in_range(values, (lower, upper), incl=False):
    """Find indices of items in `values` that are in range `(lower, upper)`."""

    if incl:
        return np.where((lower <= values) *
                        (values <= upper))[0]
    else:
        return np.where((lower <= values) *
                        (values < upper))[0]


def list_to_dict(l):
    """Build a dict of unique items in `l` associated to their coordinates."""

    out = {}

    for i, item in enumerate(l):

        if item in out:
            out[item].append(i)
        else:
            out[item] = [i]

    for k, v in out.iteritems():
        out[k] = np.array(v)

    return out


def dict_plusone(d, key):
    """Add one to `d[key]` or set to one if it does not exist."""

    if key in d:
        d[key] += 1
    else:
        d[key] = 1


def is_int(s):
    """Test if `s` represents an integer."""

    try:
        int(s)
        return True
    except ValueError:
        return False


class ProgressInfo(object):

    """Print progress information.

    A helper class to print information on the progress of an analysis,
    depending on the total number of steps and the current completed number.

    Parameters
    ----------
    n_tot : int
        Total number of steps.
    n_info : int
        Number of information messages to be printed.
    label : string, optional
        Label used for the progress information printed.

    """

    def __init__(self, n_tot, n_info, label='objects'):
        """Initialize the instance.

        Parameters
        ----------
        n_tot : int
            Total number of steps.
        n_info : int
            Number of information messages to be printed.
        label : string, optional
            Label used for the progress information printed.

        """

        self.progress = 0
        self.n_tot = n_tot
        self.info_step = max(int(round(n_tot / n_info)), 1)
        self.label = label

    def next_step(self):
        """Increase progress counter and print info if needed."""

        self.progress += 1
        if self.progress % self.info_step == 0:
            print '  {} % ({} / {} {})'.format(
                int(round(100 * self.progress / self.n_tot)), self.progress,
                self.n_tot, self.label)


def list_attributes(cls, prefix):
    """Recursively list all attributes of class `cls` beginning with
    `prefix`."""

    return set([k for scls in cls.__mro__
                for k in scls.__dict__.iterkeys()
                if re.search('^' + prefix, k)])


def list_attributes_trunc(cls, prefix):
    """Recursively list all attributes of class `cls` beginning with `prefix`,
    truncating `prefix` from the attribute names."""

    return set([k[len(prefix):] for k in list_attributes(cls, prefix)])


def dictionarize_attributes(inst, prefix):
    """Build a dict of `attr_name, attr` from `inst`'s class attributes
    beginning with `prefix`, with `attr_name` truncated from `prefix`."""

    keys = list_attributes_trunc(inst.__class__, prefix)
    return dict([(k, inst.__getattribute__(prefix + k)) for k in keys])


def iter_upper_dirs(rel_dir):
    """Iterate through parent directories of current working directory,
    appending `rel_dir` to those successive directories."""

    d = os.path.abspath('.')
    pd = None
    while pd != d:
        yield os.path.join(d, rel_dir)
        pd = d
        d = os.path.split(d)[0]


class NotFoundError(Exception):

    """Simple exception to signal a directory was not found."""

    pass


def find_upper_rel_dir(rel_dir):
    """Find a relative directory in parent directories.

    This function will search for directory `rel_dir` in all parent
    directories of the current directory.

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

    for d in iter_upper_dirs(rel_dir):
        if os.path.exists(d) and os.path.isdir(d):
            return d

    raise NotFoundError('No relative directory found in parent directories')
