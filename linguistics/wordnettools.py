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
    print 'Building transpose of Wordnet adjacency matrix (Scipy CSR)...',
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
    tM_sp = csr_matrix((np.ones(len(ij[0])), ij), shape=(num_lems, num_lems), dtype=np.float)
    print 'OK'
    
    # Compensate the weights by dividing each value by the number of outward links from
    # the corresponding word (see details of the PageRank algorithm)
    # Here we divide by the row sum (which is the same as the column sum, since the matrix is
    # symmetric), then transpose when converting to PETSc to change that into a division by column
    # sum (which is what PageRank needs). This is because column slice is inefficient in a CSR matrix.
    print 'Compensating link weights with number of outlinks...',
    for i in xrange(num_lems):
        row_vals = tM_sp.data[tM_sp.indptr[i]:tM_sp.indptr[i+1]].copy()
        tM_sp.data[tM_sp.indptr[i]:tM_sp.indptr[i+1]] = row_vals / np.sum(row_vals)
    print 'OK'
    
    # Turn it into a PETSc CSR matrix, and transpose
    print 'Converting matrix to a PETSc CSR matrix, and transposing...',
    M_pet = PETSc.Mat().create()
    M_pet.setSizes([num_lems, num_lems])
    M_pet.setType(PETSc.Mat.Type.AIJ)
    M_pet.setValuesCSR(tM_sp.indptr.copy(), tM_sp.indices.copy(), tM_sp.data.copy())
    M_pet.assemble()
    M_pet.transpose()
    del tM_sp
    print 'OK'
    
    return (lem_coords, M_pet)


def build_wn_PR_scores():
    """Compute the PageRank scores corresponding to the WN synonyms graph.
    
    Returns: a dict associating each WN lemma to its PageRank score (computed with ones on the diagonal
             of the adjacency matrix)
    
    """
    
    # Get the PETSc adjacency matrix
    lem_coords, M_pet = build_wn_PR_adjacency_matrix()
    
    # Solve the eigenvalue problem
    print 'Running SLEPc eigenproblem solver...',
    E = SLEPc.EPS()
    E.create()
    E.setOperators(M_pet)
    E.setProblemType(SLEPc.EPS.ProblemType.NHEP)
    E.setDimensions(nev=4)
    E.setTolerances(tol=1e-20, max_it=1000)
    E.solve()
    print 'OK'
    
    # Print some info about the solving process and results
    print
    print "  ******************************"
    print "  *** SLEPc Solution Results ***"
    print "  ******************************"
    print
    
    its = E.getIterationNumber()
    print "  Number of iterations of the method: %d" % its
    
    eps_type = E.getType()
    print "  Solution method: %s" % eps_type
    
    nev = E.getDimensions()[0]
    print "  Number of requested eigenvalues: %d" % nev
    
    tol, maxit = E.getTolerances()
    print "  Stopping condition: tol=%.4g, maxit=%d" % (tol, maxit)
    
    nconv = E.getConverged()
    print "  Number of converged eigenpairs %d" % nconv
    
    # Print info about converged eigenpairs, and store the results
    results = []
    if nconv > 0:
        print
        print "          k          ||Ax-kx||/||kx|| "
        print "  ----------------- ------------------"
        for i in range(nconv):
            # Create the results vectors
            vr = M_pet.getVecRight()
            vi = M_pet.getVecRight()
            k = E.getEigenpair(i, vr, vi)
            error = E.computeRelativeError(i)
            results.append((k, vr, vi, error))
            
            if k.imag != 0.0:
                print "   %9f%+9f j %12g" % (k.real, k.imag, error)
            else:
                print "   %12f    %12g" % (k.real, error)
    else:
        raise Exception('No eigenpairs converged in the SLEPc solver!')
    
    
    # Now get the proper result
    print
    print 'Taking the first eigenvector with eigenvalue 1 to have only > 0 components...',
    
    found = False
    for (k, vr, vi, error) in results:
        if k.imag == 0.0 and round(k.real, 13) == 1.0:
            scores = vr.getValues(range(len(lem_coords)))
            if np.prod(scores > 0) == True:
                found = True
                break
    if not found:
        raise Exception('No eigenvector was found for eigenvalue 1 with only > 0 components!')
    
    print 'OK'
    print 'The final result has a relative error of %12g' % error
    
    # Plug back the scores into a dict of lemmas
    print 'Replugging the PageRank scores into a dict of words...',
    lem_scores = {}
    for (w, i) in lem_coords.iteritems():
        lem_scores[w] = scores[i]
    print 'OK'
    
    return lem_scores
