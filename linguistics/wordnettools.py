#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute PageRank scores and adjacency matrices corresponding to the Wordnet synonyms graph.

Methods:
  * build_lem_coords: build a dictionary associating each lemma in Wordnet to a coordinate
  * build_wn_adjacency_matrix_Scipy: build the adjacency matrix (in Scipy Compressed Sparse Row
                                     format) for the WN synonyms graph
  * build_wn_PR_adjacency_matrix_PETSc: build the adjacency matrix (in PETSc Mat format)
                                        for the WN synonyms graph, normalized as PageRank needs
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
from scipy.sparse import csr_matrix
import numpy as np
#`from petsc4py import PETSc' in `build_wn_PR_adjacency_matrix_PETSc'
#`from slepc4py import SLEPc' in `build_wn_PR_scores'


# Module code
def build_lem_coords():
    """Build a dictionary associating each lemma in Wordnet to a coordinate.
    
    Returns: a dict which keys are the lemmas in Wordnet, and the value for a key is
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
                if not lem_coords.has_key(lem):
                    lem_coords[lem] = i
                    i += 1
    print 'OK'
    
    return lem_coords
    

def build_wn_adjacency_matrix_Scipy(lem_coords):
    """Build the adjacency matrix (in Compressed Sparse Row format) for the WN synonyms graph.
    
    Returns: the adjacency matrix, in Scipy CSR format, of the WN synonyms graph,
             with zeros on the diagonal, omitting lemmas which are not connected to any other
             (i.e. omitting lemmas that are alone in their synset)
    
    """
    
    # Build the Compressed Sparse Row matrix corresponding to the synonyms network in Wordnet
    print 'Building Wordnet adjacency matrix (Scipy CSR)...',
    # This first block of code should result in a symmetric matrix with zeros on the diagonal
    ij = ([], [])
    for syn in wn.all_synsets():
        if len(syn.lemma_names) > 1:
            for lem1 in syn.lemma_names:
                for lem2 in syn.lemma_names:
                    if lem1 != lem2:
                        ij[0].append(lem_coords[lem1])
                        ij[1].append(lem_coords[lem2])
    
    # Create the Scipy CSR matrix
    num_lems = len(lem_coords)
    tM_sp = csr_matrix((np.ones(len(ij[0])), ij), shape=(num_lems, num_lems), dtype=np.float)
    print 'OK'
    
    return tM_sp


def build_wn_PR_adjacency_matrix_PETSc(lem_coords):
    """Build the adjacency matrix (in PETSc Mat format) for the WN synonyms graph, normalized as PageRank needs.
    
    Returns: the adjacency matrix, in PETSc Matrix format, of the WN synonyms graph,
             with zeros on the diagonal, omitting lemmas which are not connected to any other
             (i.e. omitting lemmas that are alone in their synset), normalized on the columns
             (as PageRank needs it)
    
    """
    
    # Import PETSc here only, since it's a pain to install and isn't useful for other methods
    # (that way you don't need to have it to run e.g. 'build_wn_degrees')
    from petsc4py import PETSc
    
    # Build the Compressed Sparse Row matrix corresponding to the synonyms network in Wordnet
    tM_sp = build_wn_adjacency_matrix_Scipy(lem_coords)
    
    # Compensate the weights by dividing each value by the number of outward links from
    # the corresponding lemma (see details of the PageRank algorithm)
    # Here we divide by the row sum (which is the same as the column sum, since the matrix is
    # symmetric), then transpose when converting to PETSc to change that into a division by column
    # sum (which is what PageRank needs). This is because column slicing is inefficient in a CSR matrix.
    # (The 't' in 'tM_sp' stands for transpose, because the result here needs to be transposed.)
    print 'Compensating link weights with number of outlinks...',
    num_lems = len(lem_coords)
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
    
    return M_pet


def build_wn_PR_scores():
    """Compute the PageRank scores corresponding to the WN synonyms graph.
    
    Returns: a dict associating each WN lemma to its PageRank score (computed with ones on the diagonal
             of the adjacency matrix)
    
    """
    
    # Import SLEPc here only, since it's a pain to install and isn't useful for other methods
    # (that way you don't need to have it to run e.g. 'build_wn_degrees')
    from slepc4py import SLEPc
    
    # Build the lemma coordinates
    lem_coords = build_lem_coords()
    
    # Get the normalized adjacency matrix in PETSc format
    M_pet = build_wn_PR_adjacency_matrix_PETSc(lem_coords)
    
    # Solve the eigenvalue problem
    print 'Running SLEPc eigenproblem solver...',
    E = SLEPc.EPS()
    E.create()
    E.setOperators(M_pet)
    E.setProblemType(SLEPc.EPS.ProblemType.NHEP)
    E.setDimensions(nev=3)
    E.setTolerances(tol=1e-15, max_it=10000)
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
        if k.imag == 0.0 and round(k.real, 10) == 1.0:
            scores = vr.getArray()
            if np.prod(scores > 0) == True:
                found = True
                break
            elif np.prod(scores < 0) == True:
                found = True
                scores = - scores
                break
    if not found:
        raise Exception('No eigenvector was found for eigenvalue 1 with only > 0 components!')
    
    print 'OK'
    print 'The final result has a relative error of %12g' % error
    
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
    lem_coords = build_lem_coords()
    
    # Get the WN adjacency matrix in Scipy CSR format
    M_sp = build_wn_adjacency_matrix_Scipy(lem_coords)
    
    # Compute the degree of each lemma name
    print 'Computing the degree of each lemma...',
    lem_degrees = {}
    for (w, i) in lem_coords.iteritems():
        lem_degrees[w] = sum(M_sp.data[M_sp.indptr[i]:M_sp.indptr[i+1]])
    print 'OK'
    
    return lem_degrees
