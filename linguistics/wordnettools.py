#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores and adjacency matrices corresponding to the Wordnet
synonyms graph. Other tools with it.

Methods:
  * build_wn_coords: build a dictionary associating each lemma (in lowercase)
                     in Wordnet to a coordinate
  * build_wn_adjacency_matrix: build the adjacency matrix (in CSC or CSR
                               format) for the WN synonyms graph
  * build_wn_PR_scores: compute the PageRank scores corresponding to the WN
                        synonyms graph
  * build_wn_degrees: compute the degrees of lemmas in the WN graph (excluding
                      lemmas not connected to other lemmas)
  * lemmatize: lemmatize a word

The PageRank scores computed depend on the following details:
  * The adjacency matrix is built for the lemmas in WN, with zeros on the
    diagonal. Any non-linked lemma (i.e. which has no synonyms in WN) is
    removed from the matrix. The constructed matrix is symmetric before
    normalization. We then normalize on each column.

"""


from __future__ import division

from nltk.corpus import wordnet as wn
from scipy.sparse import csc_matrix, csr_matrix
import numpy as np
from scipy import random

import analyze.linalg as a_la


def build_wn_coords(pos):
    """Build a dictionary associating each lemma (in lowercase) in Wordnet to
    a coordinate.
    
    Returns: a dict which keys are the lemmas (in lowercase) in Wordnet, and
             the value for a key is the coordinate for that lemma, to be used
             e.g. with an adjacency matrix.
    
    """
    
    print 'Building lemma coordinates...',
    
    lem_coords = {}
    i = 0
    
    # Not using wn.all_lemma_names since it seems some lemmas are not in that
    # iterator creates a KeyError in the next loop, when filling ij.
    
    for syn in wn.all_synsets(pos):
        
        lemma_names_lower = set([lem.lower() for lem in syn.lemma_names])
        
        if len(lemma_names_lower) > 1:
            
            for lem in lemma_names_lower:
                
                if not lem_coords.has_key(lem):
                    
                    lem_coords[lem] = i
                    i += 1
    
    print 'OK'
    
    return lem_coords


def build_wn_adjacency_matrix(lem_coords, pos, outfmt):
    """Build the adjacency matrix (in CSC or CSR format) for the WN synonyms
    graph.
    
    Arguments:
      * lem_coords: the dict of lemma coordinates in the matrix, as return by
                    'build_wn_coords'
      * outfmt: a string specifying the compression format for the result
                matrix; can be 'csc' or 'csr'.
    
    Returns: the adjacency matrix, in Scipy CSC or CSR format, of the WN
             synonyms graph, with zeros on the diagonal, omitting lemmas which
             are not connected to any other (i.e. omitting lemmas that are
             alone in their synset).
    
    """
    
    print 'Building Wordnet adjacency matrix...',
    
    ij = ([], [])
    
    for syn in wn.all_synsets(pos):
        
        lemma_names_lower = set([lem.lower() for lem in syn.lemma_names])
        
        if len(lemma_names_lower) > 1:
            
            for lem1 in lemma_names_lower:
                
                for lem2 in lemma_names_lower:
                    
                    if lem1 != lem2:
                        
                        ij[0].append(lem_coords[lem1])
                        ij[1].append(lem_coords[lem2])
    
    # Create the Scipy CSC/CSR matrix.
    
    num_lems = len(lem_coords)
    build_matrix = {'csc': csc_matrix, 'csr': csr_matrix}
    
    M = build_matrix[outfmt]((np.ones(len(ij[0])), ij),
                             shape=(num_lems, num_lems), dtype=np.float)
    
    print 'OK'
    
    return M


def build_wn_PR_scores(pos):
    """Compute the PageRank scores corresponding to the WN synonyms graph.
    
    Returns: a dict associating each WN lemma to its PageRank score
    
    """
    
    # Build the lemma coordinates.
    
    if pos == 'all':
        pos = None
    
    lem_coords = build_wn_coords(pos)
    num_lems = len(lem_coords)
    
    # Get the normalized adjacency matrix.
    
    M = a_la.matrix_normalize_columns(build_wn_adjacency_matrix(lem_coords,
                                                                pos,
                                                                outfmt='csc'),
                                      outfmt='csr')
    
    # Solve the eigenproblem.
    
    print 'Solving the eigenproblem...',
    
    v0 = random.random(num_lems)
    v0 = v0 / a_la.norm_l1(v0)
    (scores, nit, prec) = a_la.matrix_eigen_solve(M, v0=v0,
                                                  max_it=10000, tol=1e-15)
    
    print 'OK'
    
    # Some info on the results.
    
    print
    print '*** Results ***'
    print '  Number of iterations:', nit
    print '  Final precision:', prec
    
    # Plug back the scores into a dict of lemmas.
    
    print 'Replugging the PageRank scores into a dict of lemmas...',
    
    lem_scores = {}
    
    for (w, i) in lem_coords.iteritems():
        lem_scores[w] = scores[i]
    
    print 'OK'
    
    return lem_scores


def build_wn_degrees(pos):
    """Compute the degrees of lemmas in the WN graph (excluding lemmas not
    connected to other lemmas).
    
    Returns: a dict associating each lemma to its degree.
    
    """
    
    # Build the lemma coordinates.
    
    if pos == 'all':
        pos = None
    
    lem_coords = build_wn_coords(pos)
    
    # Get the WN adjacency matrix in Scipy CSC format.
    
    M = build_wn_adjacency_matrix(lem_coords, pos, outfmt='csc')
    
    # Compute the degree of each lemma name.
    
    print 'Computing the degree of each lemma...',
    
    lem_degrees = {}
    
    for (w, i) in lem_coords.iteritems():
        lem_degrees[w] = sum(M.data[M.indptr[i]:M.indptr[i+1]])
    
    print 'OK'
    
    return lem_degrees


def truncate_wn_features(features, pos):
    """Truncate a dict of WN features to the words with POS == pos."""
    if pos == 'all':
        return features
    
    lem_coords = build_wn_coords(pos)
    new_features = {}
    
    for lem in lem_coords.iterkeys():
        new_features[lem] = features[lem]
    
    return new_features


def lemmatize(word):
    """Lemmatize a word."""
    morph = wn.morphy(word)
    return morph if morph != None else word
