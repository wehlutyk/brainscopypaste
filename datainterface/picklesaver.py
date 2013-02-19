#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Save or load any data in pickle format."""


import cPickle
import copy_reg
import types

import numpy as np


#
# This little hack lets us pickle instancemethods
#

# ----- start hack -----

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

# ----- end hack -----


def save(s, filepath):
    """Save a structure to a file.

    Parameters
    ----------
    s : picklable
        The structure to save.
    filepath : string
        Full path to the file to save to.

    """

    with open(filepath, 'wb') as f:
        cPickle.dump(s, f, cPickle.HIGHEST_PROTOCOL)


def load(filepath):
    """Load a structure from a file.

    Parameters
    ----------
    filepath : string
        Full path to the file to load from.

    Returns
    -------
    s : picklable
        The loaded structure.

    """

    with open(filepath, 'rb') as f:
        s = cPickle.load(f)

    return s


def npsave(s, filepath):
    """Save a :class:`numpy.ndarray` to a file using numpy's dedicated method.

    Parameters
    ----------
    s : :class:`numpy.ndarray`
        The array to save.
    filepath : string
        Full path to the file to save to.

    """

    with open(filepath, 'wb') as f:
        np.save(f, s)


def npload(filepath):
    """Load a :class:`numpy.ndarray` from a file using numpy's dedicated
    method.

    Parameters
    ----------
    filepath : string
        Full path to the file to load from.

    Returns
    -------
    s : :class:`numpy.ndarray`
        The loaded array.

    """

    with open(filepath, 'rb') as f:
        s = np.load(f)

    return s
