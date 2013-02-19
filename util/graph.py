#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Graph exploring utilities.

These methods are used to recursively explore neighbors of a node in a graph.

"""


from functools import partial

from .generic import memoize


def _walk_neighbors(G, node, depth, l):
    """Recursive worker function for :func:`walk_neighbors`."""

    l.add(node)
    if depth > 0:
        for n in G.neighbors_iter(node):
            _walk_neighbors(G, n, depth - 1, l)


def walk_neighbors(G, node, depth):
    """Recursively list neighbors of `node` up to depth `depth`.

    Parameters
    ----------
    G : networkx.Graph
        Graph to explore.
    node : immutable object
        Name of the node from which to explore neighbors.
    depth : int
        Depth to which neighbors are to be searched for.

    Returns
    -------
    out : set
        `set` of nodes at distance `<= depth` from `node`.

    """

    out = set([])
    _walk_neighbors(G, node, depth, out)
    return out


def caching_neighbors_walker(G):
    """Build a caching function for :func:`walk_neighbors` on graph `G`.

    Parameters
    ----------
    G : networkx.Graph
        Graph to work on.

    Returns
    -------
    out : function
        A caching version of :func:`walk_neighbors` without the `G` parameter.

    """

    return memoize(partial(walk_neighbors, G))
