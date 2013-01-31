#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Various utility methods.

The methods in this module manipulate lists, dicts, and classes. The
package also contains methods for exploring a graph, some linear algebra,
and heck-like helpers to ease logging with multiprocessing.

"""


import re

import numpy as np


def memoize(func):
    """Wrap `func` in a caching method."""

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

        if out.has_key(item):
            out[item].append(i)
        else:
            out[item] = [i]

    for k, v in out.iteritems():
        out[k] = np.array(v)

    return out


def dict_plusone(d, key):
    """Add one to `d[key]` or set to one if it does not exist."""

    if d.has_key(key):
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

    Methods
    -------
    next_step()
        Increase progress counter and print info if needed.

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
    beginning with `prefix`, with `attr_name` is truncated from `prefix`."""

    keys = list_attributes(inst.__class__, prefix)
    return dict([(k[len(prefix):], inst.__getattribute__(k))
                 for k in keys])
