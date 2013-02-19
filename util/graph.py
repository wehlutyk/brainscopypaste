from functools import partial

from .generic import memoize


def _walk_neighbors(G, node, depth, l):
    l.add(node)
    if depth > 0:
        for n in G.neighbors_iter(node):
            _walk_neighbors(G, n, depth - 1, l)


def walk_neighbors(G, node, depth):
    out = set([])
    _walk_neighbors(G, node, depth, out)
    return out


def caching_neighbors_walker(G):
    return memoize(partial(walk_neighbors, G))
