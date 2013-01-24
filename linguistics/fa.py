#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores and adjacency matrices corresponding to the Free
Association norms.

Methods:
  * build_fa_coords: build a dictionary associating each normed word (in
                     lowercase) in the Free Association norms to a coordinate
  * build_fa_adjacency_matrix: build the adjacency matrix (in CSC or CSR
                               format) for the Free Association graph
  * build_fa_PR_scores: compute the PageRank scores corresponding to the Free
                        Association graph

"""


from __future__ import division

from scipy.sparse import csc_matrix, csr_matrix
import numpy as np
from scipy import random
import networkx as nx

import datainterface.picklesaver as ps
from util import memoize
import util.linalg as u_la
import settings as st


def _load_fa_norms():
    print 'Loading Free Association norms from pickle...',
    norms = ps.load(st.fa_norms_pickle)
    print 'OK'
    return norms


load_fa_norms = memoize(_load_fa_norms)


def _build_fa_coords():
    """Build a dictionary associating each normed word (in lowercase) in the
    Free Association norms to a coordinate.

    Returns: a dict associating each normed word to its coordinate.

    """

    norms = load_fa_norms()

    print 'Building word coordinates...',

    word_coords = {}
    i = 0

    for w in norms.iterkeys():

        word_coords[w] = i
        i += 1

    print 'OK'

    return word_coords


build_fa_coords = memoize(_build_fa_coords)


def build_fa_adjacency_matrix(word_coords, outfmt):
    """Build the adjacency matrix (in CSC or CSR format) for the Free
    Association graph.

    Arguments:
      * word_coords: the dict of coordinates for the norms (as created by
                     'build_fa_coords')
      * outfmt: a string specifying the compression format for the result
                matrix; can be 'csc' or 'csr'.

    Returns: the adjacency matrix, in Scipy CSC or CSR format, of the Free
             Association graph.
    """

    norms = load_fa_norms()

    print 'Building Free Association adjacency matrix...',

    ij = ([], [])
    data = []

    for w1, assoc in norms.iteritems():

        for (w2, ref, weight) in assoc:

            if ref:

                ij[1].append(word_coords[w1])
                ij[0].append(word_coords[w2])
                data.append(weight)

    # Create the Scipy CSC/CSR matrix.

    num_words = len(word_coords)
    build_matrix = {'csc': csc_matrix, 'csr': csr_matrix}

    M = build_matrix[outfmt]((data, ij),
                             shape=(num_words, num_words), dtype=np.float)

    print 'OK'

    return M


def _build_fa_nxgraph():

    print 'Building NX graph...',

    lem_coords = build_fa_coords()
    M = build_fa_adjacency_matrix(lem_coords, outfmt='csc')
    G =  nx.from_scipy_sparse_matrix(M)

    print 'OK'
    return (lem_coords, G)


build_fa_nxgraph = memoize(_build_fa_nxgraph)


def build_fa_PR_scores():
    """Compute the PageRank scores corresponding to the Free Association
    graph.

    Returns: a dict associating each normed word to its PageRank score.

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

    Returns: a dict associating each lemma to its BC.

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
