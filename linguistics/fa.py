#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores and adjacency matrices corresponding to the Free
Association norms."""


from __future__ import division

from scipy.sparse import csc_matrix, csr_matrix
import numpy as np
from scipy import random
import networkx as nx

import datainterface.picklesaver as ps
from util.generic import inv_dict, memoize
import util.linalg as u_la
import settings as st


def _load_fa_norms():
    """Load Free Association norms from pickle file, and return them.

    See Also
    --------
    load_fa_norms

    """

    print 'Loading Free Association norms from pickle...',
    norms = ps.load(st.fa_norms_pickle)
    print 'OK'
    return norms


load_fa_norms = memoize(_load_fa_norms)
"""Caching version of :meth:`_load_fa_norms`, recommended to use over the
latter."""


def _build_fa_coords():
    """Build a dictionary associating each normed word (in lowercase) in the
    Free Association norms to a coordinate.

    Returns
    -------
    dict
        The association of each normed word to its coordinate.

    See Also
    --------
    build_fa_coords

    """

    norms = load_fa_norms()

    print 'Building word coordinates...',

    word_coords = {}
    i = 0

    for w1, assoc in norms.iteritems():

        for w2, ref, weight in assoc:

            if w1 not in word_coords:
                word_coords[w1] = i
                i += 1

            if w2 not in word_coords:
                word_coords[w2] = i
                i += 1

    print 'OK'

    return word_coords


build_fa_coords = memoize(_build_fa_coords)
"""Caching version of :meth:`_build_fa_coords`, recommended to use over the
latter."""


def build_fa_adjacency_matrix(word_coords, outfmt):
    """Build the adjacency matrix (in :class:`~scipy.sparse.csc_matrix` or
    :class:`~scipy.sparse.csr_matrix` format) for the Free Association graph.

    Parameters
    ----------
    word_coords : dict
        Coordinates for the norms (as created by :meth:`build_fa_coords`).
    outfmt : string
        Compression format for the result matrix; either 'csc' or 'csr'.

    Returns
    -------
    csc_matrix or csr_matrix
        The adjacency matrix, in :class:`~scipy.sparse.csc_matrix` or
        :class:`~scipy.sparse.csr_matrix` format, of the Free
        Association graph.

    """

    norms = load_fa_norms()

    print 'Building Free Association adjacency matrix...',

    ij = ([], [])

    for w1, assoc in norms.iteritems():

        for (w2, ref, weight) in assoc:

            ij[1].append(word_coords[w1])
            ij[0].append(word_coords[w2])

    # Create the Scipy CSC/CSR matrix.

    num_words = len(word_coords)
    build_matrix = {'csc': csc_matrix, 'csr': csr_matrix}

    M = build_matrix[outfmt]((np.ones(len(ij[0])), ij),
                             shape=(num_words, num_words), dtype=np.float)

    print 'OK'

    return M


def _build_fa_nxgraph():
    """Build the undirected :func:`networkx.Graph` for the Free Association
    network.

    See Also
    --------
    build_fa_nxgraph

    """

    print 'Building Undirected NX graph...',

    lem_coords = build_fa_coords()
    M = build_fa_adjacency_matrix(lem_coords, outfmt='csc')
    # The format for loading into nx is transposed from scipy's, but this isn't
    # important here since we're symetrising the graph anyway
    # (from_scipy_sparse_matrix creates a undirected graph unless instructed
    # otherwise)
    G = nx.from_scipy_sparse_matrix(M.transpose())

    print 'OK'
    return (lem_coords, G)


build_fa_nxgraph = memoize(_build_fa_nxgraph)
"""Caching version of :meth:`_build_fa_nxgraph`, recommended to use over the
latter."""


def build_fa_PR_scores():
    """Compute the PageRank scores corresponding to the Free Association
    graph.

    Returns
    -------
    dict
        The association of each normed word to its PageRank score.

    """

    # Build the word coordinates.

    word_coords = build_fa_coords()
    num_words = len(word_coords)

    # Get the normalized adjacency matrix.

    M = u_la.matrix_normalize_columns(build_fa_adjacency_matrix(word_coords,
                                                                outfmt='csc'),
                                      outfmt='csr')

    # Solve the eigenproblem.

    print 'Solving the eigenproblem...',

    v0 = random.random(num_words)
    v0 = v0 / u_la.norm_l1(v0)
    damp_v = np.ones(num_words) / num_words
    (scores, nit, prec) = u_la.matrix_eigen_solve(M, v0=v0,
                                                  max_it=10000, tol=1e-15,
                                                  damp_v=damp_v, d=0.9)

    print 'OK'

    # Some info on the results.

    print
    print '*** Results ***'
    print '  Number of iterations:', nit
    print '  Final precision:', prec

    # Plug back the scores into a dict of words.

    print 'Replugging the PageRank scores into a dict of words...',

    word_scores = {}

    for (w, i) in word_coords.iteritems():
        word_scores[w] = scores[i]

    print 'OK'

    return word_scores


def build_fa_BCs():
    """Compute betweenness centrality of lemmas in the FA graph.

    Returns
    -------
    dict
        The association of each lemma to its BC.

    """

    # Build the lemma coordinates.

    lem_coords, G = build_fa_nxgraph()

    print 'Computing the BC of each lemma...',

    BCs = nx.betweenness_centrality(G)

    lem_BCs = {}

    for w, i in lem_coords.iteritems():
        if BCs[i] > 0:
            lem_BCs[w] = BCs[i]

    print 'OK'

    return lem_BCs


def build_fa_degrees():
    """Compute the degrees of lemmas in the FA graph.

    Returns
    -------
    dict
        The association of each lemma to its degree.

    """

    lem_coords, G = build_fa_nxgraph()

    print 'Computing degree of each lemma...',

    degrees = {}

    for w, i in lem_coords.iteritems():
        if G.degree(i) > 0:
            degrees[w] = G.degree(i)

    return degrees


def build_fa_CCs():
    """Compute clustering coefficients of lemmas in the FA graph.

    Returns
    -------
    dict
        The association of each lemma to its CC.

    """

    # Build the lemma coordinates.

    lem_coords, G = build_fa_nxgraph()

    print 'Computing the CC of each lemma...',

    CCs = nx.clustering(G)

    lem_CCs = {}

    for w, i in lem_coords.iteritems():
        if CCs[i] > 0:
            lem_CCs[w] = CCs[i]

    print 'OK'

    return lem_CCs


def build_fa_paths():
    """Compute the shortest paths between each pair in the FA graph.

    Returns
    -------
    dict
        Dictionary of shortest path lengths keyed by source and target.

    """

    lem_coords, G = build_fa_nxgraph()
    inv_coords = inv_dict(lem_coords)

    print 'Computing the shortest paths between each lemma pair...',

    G = nx.relabel_nodes(G, inv_coords)
    path_lengths = nx.all_pairs_shortest_path_length(G)

    print 'OK'

    return path_lengths


def build_fa_paths_distribution(path_lengths):
    """Compute the distribution of path lengths in the FA graph.

    Parameters
    ----------
    path_lengths : dict
        The dictionary of path lengths between pairs as computed by
        :meth:`build_fa_paths`.

    Returns
    -------
    np.array
        The distribution of path lengths, where the index in the array
        is the path length in question.

    """

    lengths_all = []
    for d in path_lengths.itervalues():
        lengths_all.extend(d.values())
    lengths_all = np.array(lengths_all, dtype=np.uint8)

    bins = np.arange(lengths_all.min(), lengths_all.max() + 2) - 0.5
    distribution = np.histogram(lengths_all, bins=bins, normed=True)[0]

    return distribution
