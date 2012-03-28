#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores corresponding to the Wordnet synonyms graph.

Methods:
  * build_wn_PR_adjacency_matrix: build the adjacency matrix (in Compressed Sparse Row format) for the WN synonyms graph
  * build_wn_PR_scores: compute the PageRank scores corresponding to the WN synonyms graph

"""


# Imports
from __future__ import division
from nltk.corpus import wordnet as wn
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigs
import numpy as np
from petsc4py import PETSc
from slepc4py import SLEPc


# Module code
def build_wn_PR_adjacency_matrix():
    """Build the adjacency matrix (in Compressed Sparse Row format) for the WN synonyms graph.
    
    Returns: a tuple (lem_coords, M_sp):
      * lem_coords: a dict associating each lemma to its coordinate in the adjacency matrix
      * M_sp: the adjacency matrix, in CSR format, of the WN synonyms graph, with ones on the diagonal
    
    """
    
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
    print 'Building Wordnet adjacency matrix (Scipy CSR)...',
    # This first loop should result in a symmetric matrix with zeros on the diagonal
    ij = ([], [])
    for syn in wn.all_synsets():
        for lem1 in syn.lemma_names:
            for lem2 in syn.lemma_names:
                if lem1 != lem2:
                    ij[0].append(lem_coords[lem1])
                    ij[1].append(lem_coords[lem2])
    # Set the diagonal
    for i in xrange(num_lems):
        ij[0].append(i)
        ij[1].append(i)
    # Create the Scipy CSR matrix
    M_sp = csr_matrix((np.ones(len(ij[0])), ij), shape=(num_lems, num_lems), dtype=np.float)
    print 'OK'
    
    # Compensate the weights by dividing each value by the number of outward links from
    # the corresponding word (see details of the PageRank algorithm)
    # Here we divide by the row sum (which is the same as the column sum, since the matrix is
    # symmetric), then transpose to change that into a division by column sum (which is what
    # PageRank does). This is because column sum is inefficient in a CSR matrix.
    print 'Compensating link weights with number of outlinks...',
    for i in xrange(num_lems):
        row_vals = M_sp.data[M_sp.indptr[i]:M_sp.indptr[i+1]].copy()
        M_sp.data[M_sp.indptr[i]:M_sp.indptr[i+1]] = row_vals / np.sum(row_vals)
    M_sp = M_sp.transpose()
    print 'OK'
    
    # Turn it into a PETSc CSR matrix
    print 'Converting matrix to a PETSc CSR matrix...',
    M_pet = PETSc.Mat().create()
    M_pet.setSizes([num_lems, num_lems])
    M_pet.setType(PETSc.Mat.Type.AIJ)
    M_pet.setValuesCSR(M_sp.indptr.copy(), M_sp.indices.copy(), M_sp.data.copy())
    M_pet.assemble()
    del M_sp
    print 'OK'
    
    return (lem_coords, M_pet)


def build_wn_PR_scores():
    """Compute the PageRank scores corresponding to the WN synonyms graph.
    
    Returns: a dict associating each WN lemma to its PageRank score (computed with ones on the diagonal
             of the adjacency matrix)
    
    """
    
    # Get the PETSc adjacency matrix
    (lem_coords, M_pet) = build_wn_PR_adjacency_matrix()
    
    # Solve the eigenvalue problem
    print 'Computing first matrix eigenvector...',
    E = SLEPc.EPS()
    E.create()
    E.setOperators(M_pet)
    E.setProblemType(SLEPc.EPS.ProblemType.NHEP)
    E.setDimensions(nev=2)
    E.setTolerances(tol=1e-15, max_it=1000)
    E.solve()
    print 'OK'
    
    print
    print "******************************"
    print "*** SLEPc Solution Results ***"
    print "******************************"
    print
    
    its = E.getIterationNumber()
    print "Number of iterations of the method: %d" % its
    
    eps_type = E.getType()
    print "Solution method: %s" % eps_type
    
    nev, ncv, mpd = E.getDimensions()
    print "Number of requested eigenvalues: %d" % nev
    
    tol, maxit = E.getTolerances()
    print "Stopping condition: tol=%.4g, maxit=%d" % (tol, maxit)
    
    nconv = E.getConverged()
    print "Number of converged eigenpairs %d" % nconv
    
    if nconv > 0:
        # Create the results vectors
        vr, wr = M_pet.getVecs()
        vi, wi = M_pet.getVecs()
        
        print
        print "        k          ||Ax-kx||/||kx|| "
        print "----------------- ------------------"
        for i in range(nconv):
            k = E.getEigenpair(i, vr, vi)
            error = E.computeRelativeError(i)
            if k.imag != 0.0:
                print " %9f%+9f j %12g" % (k.real, k.imag, error)
            else:
                print " %12f    %12g" % (k.real, error)
    print

    
    # Plug back the scores into a dict of lemmas
#    print 'Replugging the PageRank scores into a dict of words...',
#    lem_scores = {}
#    for (w, i) in lem_coords.iteritems():
#        lem_scores[w] = np.real(score_list[i])
#    print 'OK'
#    
#    return lem_scores
