import re

import numpy as np


def memoize(func):
    cache = {}
    def inner(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return inner


def inv_dict(d):
    inv_d = {}
    for k, v in d.iteritems():
        inv_d[v] = k
    return inv_d


def indices_in_range(values, (lower, upper), incl=False):
    if incl:
        return np.where((lower <= values) *
                        (values <= upper))[0]
    else:
        return np.where((lower <= values) *
                        (values < upper))[0]


def list_to_dict(l):
    """Convert a list of numbers to a dict associating each single item to an
    array of its coordinates."""
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
    """Add one to d[key] or set it to one if non-existent."""
    if d.has_key(key):
        d[key] += 1
    else:
        d[key] = 1


def is_int(s):
    """Test if a string represents an integer."""
    try:
        int(s)
        return True
    except ValueError:
        return False


class ProgressInfo(object):

    """Print progress information.

    Methods:
      * __init__: initialize the instance
      * next_step: increase progress counter and print info if needed

    """

    def __init__(self, n_tot, n_info, label='objects'):
        """Initialize the instance.

        Arguments:
          * n_tot: the total number of items through which we are making
                   progress
          * n_info: the number of informations messages to be displayed

        Keyword arguments:
          * label: a label for printing information (i.e. what kind of objects
                   are we making progress through?). Defaults to 'objects'.

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
    return set([k for scls in cls.__mro__
                for k in scls.__dict__.iterkeys()
                if re.search('^' + prefix, k)])


def list_attributes_trunc(cls, prefix):
    return set([k[len(prefix):] for k in list_attributes(cls, prefix)])


def dictionarize_attributes(inst, prefix):
    keys = list_attributes(inst.__class__, prefix)
    return dict([(k[len(prefix):], inst.__getattribute__(k))
                 for k in keys])

