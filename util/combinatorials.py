#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Combinatorial tools, used particularly when working with quote transitions.

These methods are used to build Combinatorial lists of tuples.

"""


def _build_ordered_tuples(indices_range, tuples):
    """Recursively build the list of all possible ordered tuples with values
    in `indices_range`.

    This is the recursive worker function for :func:`build_ordered_tuples`.
    It adds the built tuples to `tuples`.

    Parameters
    ----------
    indices_range : list of ints
        Range of indices from which to build the tuples.
    tuples : list of tuples
        List of tuples passed on to the recursive instances of the method,
        containing what tuples have already been generated.

    See Also
    --------
    build_ordered_tuples

    """

    if len(indices_range) > 1:

        tuples.extend([(indices_range[0], idx) for idx in indices_range[1:]])
        _build_ordered_tuples(indices_range[1:], tuples)

    else:
        return []


def build_ordered_tuples(indices_max):
    """Build the list of all possible ordered tuples with values between zero
    and `indices_max` (excluded).

    Parameters
    ----------
    indices_max : int
        Top limit to the tuple values.

    Returns
    -------
    tuples : list of tuples
        Full list of all possible ordered tuples with values between zero and
        `indices_max`.

    """

    tuples = []
    _build_ordered_tuples(range(indices_max), tuples)

    return tuples
