#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores and adjacency matrices corresponding to the Wordnet synonyms graph.

Methods:
  * build_wn_coords: build a dictionary associating each lemma (in lowercase) in Wordnet to a coordinate
  * build_wn_adjacency_matrix: build the adjacency matrix (in CSC or CSR format) for
                               the WN synonyms graph
  * matrix_normalize_columns: Normalize a CSC or CSR matrix on its columns, and return in
                              'outfmt' format ('csc' or 'csr')
  * norm_l1: compute the l1 norm of an array
  * matrix_eigen_solve: solve the v = M*v eigenproblem by the Power Iteration algorithm
  * build_wn_PR_scores: compute the PageRank scores corresponding to the WN synonyms graph
  * build_wn_degrees: compute the degrees of lemmas in the WN graph (not excluding lemmas not
                      connected to other lemmas)

The PageRank scores computed depend on the following details:
  * The adjacency matrix is built for the lemmas in WN, with zeros on the diagonal. Any non-linked
    lemma (i.e. which has no synonyms in WN) is removed from the matrix. The constructed matrix is
    symmetric before normalization. We then normalize on each column.
  * The solution of the eigenproblem may not be unique (the matrix need not have a 1-dimensional
    eigenspace associated to the eigenvalue 1, and if it does the approximation in computation could
    break that), but is computed with a 1e-15 tolerance.

"""


# Imports
from __future__ import division
from nltk.corpus import wordnet as wn
from scipy.sparse import csc_matrix, csr_matrix
import numpy as np
from scipy import random


# Module code
def build_wn_coords():
    """Build a dictionary associating each lemma (in lowercase) in Wordnet to a coordinate.
    
    Returns: a dict which keys are the lemmas (in lowercase) in Wordnet, and the value for a key is
             the coordinate for that lemma, to be used e.g. with an adjacency matrix.
    
    """
    
    print 'Building lemma coordinates...',
    lem_coords = {}
    i = 0
    # Not using wn.all_lemma_names since it seems some lemmas are not in that iterator
    # creates a KeyError in the next loop, when filling ij
    for syn in wn.all_synsets():
        if len(syn.lemma_names) > 1:
            for lem in syn.lemma_names:
                if not lem_coords.has_key(lem.lower()):
                    lem_coords[lem.lower()] = i
                    i += 1
    print 'OK'
    
    return lem_coords
    

def build_wn_adjacency_matrix(lem_coords, outfmt):
    """Build the adjacency matrix (in CSC or CSR format) for the WN synonyms graph.
    
    Arguments:
      * lem_coords: the dict of lemma coordinates in the matrix, as return by 'build_wn_coords'
      * outfmt: a string specifying the compression format for the result matrix ; can be 'csc' or 'csr'.
    
    Returns: the adjacency matrix, in Scipy CSC or CSR format, of the WN synonyms graph,
             with zeros on the diagonal, omitting lemmas which are not connected to any other
             (i.e. omitting lemmas that are alone in their synset)
    
    """
    
    # Build the Compressed Sparse Column/Row matrix corresponding to the synonyms network in Wordnet
    print 'Building Wordnet adjacency matrix...',
    # This first block of code should result in a symmetric matrix with zeros on the diagonal
    ij = ([], [])
    for syn in wn.all_synsets():
        if len(syn.lemma_names) > 1:
            for lem1 in syn.lemma_names:
                for lem2 in syn.lemma_names:
                    if lem1.lower() != lem2.lower():
                        ij[0].append(lem_coords[lem1.lower()])
                        ij[1].append(lem_coords[lem2.lower()])
    
    # Create the Scipy CSC/CSR matrix
    num_lems = len(lem_coords)
    build_matrix = {'csc': csc_matrix, 'csr': csr_matrix}
    M = build_matrix[outfmt]((np.ones(len(ij[0])), ij), shape=(num_lems, num_lems), dtype=np.float)
    print 'OK'
    
    return M


def matrix_normalize_columns(M, outfmt):
    """Normalize a CSC or CSR matrix on its columns, and return in 'outfmt' format ('csc' or 'csr')."""
    
    # If the matrix is CSR, convert to CSC
    if M.getformat() == 'csr':
        M = M.tocsc()
    
    # Normalize on the columns
    print 'Normalizing matrix on the columns...',
    num_lems = M.get_shape()[0]
    for i in xrange(num_lems):
        col_vals = M.data[M.indptr[i]:M.indptr[i+1]].copy()
        M.data[M.indptr[i]:M.indptr[i+1]] = col_vals / np.sum(col_vals)
    print 'OK'
    
    # Convert to outfmt if necessary
    if outfmt == 'csr':
        M = M.tocsr()
    elif outfmt != 'csc':
        raise Exception("Unrecognized matrix format: '{}'".format(outfmt))
    
    return M


def norm_l1(v):
    """Compute the l1 norm of an array."""
    return np.sum(np.abs(v))


def matrix_eigen_solve(M, v0, max_it, tol):
    """Solve the v = M*v eigenproblem by the Power Iteration algorithm.
    
    This will only work on a stochastic matrix, since there is no vector renormalization
    (it created precision problems). Note that to avoid oscillation in the algorithm, each
    iteration consists in fact of a random number (1-9) of iterations.
    
    Arguments:
      * M: the matrix for the eigenproblem, preferably in CSR format
      * v0: a starting vector for the iteration ; should be normalized
      * max_it: the maximum number of iterations that will be performed
      * tol: the relative precision requested
    
    Returns: a tuple consisting of:
      * vv: the final eigenvector
      * nit: the number of iterations completed
      * prec: the final relative precision
    
    """
    
    # Initialize
    v = v0.copy()
    vv = M.dot(M.dot(v))
    nit = 0
    
    # Loop until we reach the tolerance
    while norm_l1(vv - v) >= tol:
        
        # Do the iteration calculus
        v = vv
        for i in range(random.randint(1, 10)):
            vv = M.dot(M.dot(vv))
        
        # Or until we do too many iterations
        nit += 1
        if nit >= max_it:
            break
    
    # Return the solution, along with convergence information
    return (vv, nit, norm_l1(vv - v))


def build_wn_PR_scores():
    """Compute the PageRank scores corresponding to the WN synonyms graph.
    
    Returns: a dict associating each WN lemma to its PageRank score (computed with ones on the diagonal
             of the adjacency matrix)
    
    """
    
    # Build the lemma coordinates
    lem_coords = build_wn_coords()
    num_lems = len(lem_coords)
    
    # Get the normalized adjacency matrix
    M = matrix_normalize_columns(build_wn_adjacency_matrix(lem_coords, outfmt='csc'), outfmt='csr')
    
    # Solve the eigenproblem
    print 'Solving the eigenproblem...',
    v0 = random.random(num_lems)
    v0 = v0 / norm_l1(v0)
    (scores, nit, prec) = matrix_eigen_solve(M, v0=v0, max_it=10000, tol=1e-10)
    print 'OK'
    
    # Some info on the results
    print
    print '*** Results ***'
    print '  Number of iterations:', nit
    print '  Final precision:', prec
    
    # Plug back the scores into a dict of lemmas
    print 'Replugging the PageRank scores into a dict of lemmas...',
    lem_scores = {}
    for (w, i) in lem_coords.iteritems():
        lem_scores[w] = scores[i]
    print 'OK'
    
    return lem_scores


def build_wn_degrees():
    """Compute the degrees of lemmas in the WN graph (not excluding lemmas not connected to other lemmas).
    
    Returns: a dict associating each lemma to its degree
    
    """
    
    # Build the lemma coordinates
    lem_coords = build_wn_coords()
    
    # Get the WN adjacency matrix in Scipy CSC format
    M = build_wn_adjacency_matrix(lem_coords, outfmt='csc')
    
    # Compute the degree of each lemma name
    print 'Computing the degree of each lemma...',
    lem_degrees = {}
    for (w, i) in lem_coords.iteritems():
        lem_degrees[w] = sum(M.data[M.indptr[i]:M.indptr[i+1]])
    print 'OK'
    
    return lem_degrees
