#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Combinatorial tools, used particularly when working with quote transitions.

These methods are used to build Combinatorial lists of tuples.

"""


def _build_ordered_tuples(indices_range, tuples):
    """Recursively build the list of all possible ordered tuples with values
    in a certain range.

    Arguments:
      * indices_range: the range of indices from which to build the tuples
      * tuples: the list of tuples passed on to the recursive instances of the
                method, containing what tuples have already been generated

    Returns: a list of tuples.

    """

    if len(indices_range) > 1:

        tuples.extend([(indices_range[0], idx) for idx in indices_range[1:]])
        _build_ordered_tuples(indices_range[1:], tuples)

    else:
        return []


def build_ordered_tuples(indices_max):
    """Build the list of all possible ordered tuples with values below
    indices_max.

    The real work is done by the '_build_ordered_tuples' method.

    Arguments:
      * indices_max: the top limit to the tuple values

    Returns: a list of tuples.

    """

    tuples = []
    _build_ordered_tuples(range(indices_max), tuples)

    return tuples
