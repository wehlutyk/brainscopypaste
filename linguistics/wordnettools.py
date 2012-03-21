#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TODO: this module needs documenting
TODO: there's a problem somewhere... I get negative PR scores (e.g. for 'will', 'can')
"""


# Imports
from __future__ import division
from nltk.corpus import wordnet as wn
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import numpy as np


# Module code
def build_wn_symmetric_connectivity_csrmatrix():
    # Build the dictionary of word coordinates
    print 'Building word coordinates...',
    lem_coords = {}
    i = 0
    # Not using wn.all_lemma_names since it seems some lemmas are not in that iterator
    # creates a KeyError in the next loop, when filling ij
    for syn in wn.all_synsets():
        for lem in syn.lemma_names:
            if not lem_coords.has_key(lem):
                lem_coords[lem] = i
                i += 1
    num_lems = len(lem_coords)
    print 'OK'
    
    # Build the Compressed Sparse Row matrix corresponding to the synonyms network in Wordnet
    # This should yield a symmetric matrix with zeros on the diagonal
    print 'Building Wordnet connectivity matrix...',
    ij = ([], [])
    for syn in wn.all_synsets():
        for lem1 in syn.lemma_names:
            for lem2 in syn.lemma_names:
                if lem1 != lem2:
                    ij[0].append(lem_coords[lem1])
                    ij[1].append(lem_coords[lem2])
    Mwn_csr = csr_matrix(([1]*len(ij[0]), ij), shape=(num_lems, num_lems), dtype=np.float)
    print 'OK'
    
    # Compensate the weights by dividing each value by the number of outward links from
    # the corresponding word (see details of the PageRank algorithm)
    # The following implementation corresponds to PageRank ONLY IF the matrix is indeed symmetric
    # (since PageRank divides by the sum of column, not line)
    print 'Compensating link weights with number of outlinks...',
    for i in xrange(num_lems):
        n_out = Mwn_csr.indptr[i+1] - Mwn_csr.indptr[i]
        Mwn_csr.data[Mwn_csr.indptr[i]:Mwn_csr.indptr[i+1]] = Mwn_csr.data[Mwn_csr.indptr[i]:Mwn_csr.indptr[i+1]] / n_out
    print 'OK'
    
    return (lem_coords, Mwn_csr)


def build_wn_PR_scores():
    # Get the connectivity matrix
    (lem_coords, Mwn_csr) = build_wn_symmetric_connectivity_csrmatrix()
    
    # Compute the PageRank scores
    print 'Computing first matrix eigenvector...',
    score_list = eigsh(Mwn_csr, 1, which='LM')[1]
    print 'OK'
    
    # Plug back the correspondance of words with scores
    print 'Replugging the PageRank scores into a dict of words...'
    lem_scores = {}
    for (w, i) in lem_coords.iteritems():
        lem_scores[w] = score_list[i]
    print 'OK'
    
    return lem_scores
