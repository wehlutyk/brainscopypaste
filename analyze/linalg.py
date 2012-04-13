#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Linear algebra tools, specifically to compute the PageRank algorithm.

Methods:
  * matrix_normalize_columns: Normalize a CSC or CSR matrix on its columns
  * norm_l1: compute the l1 norm of an array
  * matrix_eigen_solve: solve the v = M*v eigenproblem by the Power Iteration
                        algorithm

"""


from __future__ import division

import numpy as np
from scipy import random


def matrix_normalize_columns(M, outfmt):
    """Normalize a CSC or CSR matrix on its columns.
    
    Arguments:
      * outfmt: the output format for the normalized matrix. Accepted values
                are 'csc' and 'csr'.
    
    """
    
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
    
    This will only work on a stochastic matrix, since there is no vector
    renormalization (it creates precision problems). Note that to avoid
    oscillation in the algorithm, each iteration consists in fact of a random
    number (1-9) of iterations.
    
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
    
    # Return convergence information with the solution
    
    return (vv, nit, norm_l1(vv - v))
