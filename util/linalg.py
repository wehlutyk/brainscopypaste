#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Linear algebra tools, specifically to compute the PageRank algorithm.

These methods allow for computation of the PageRank of nodes in a graph
using the `Power Iteration <http://en.wikipedia.org/wiki/Power_iteration>`_
algorithm.

"""


from __future__ import division

import numpy as np
from scipy import random


def matrix_normalize_columns(M, outfmt):
    """Normalize a CSC or CSR matrix on its columns.

    Parameters
    ----------
    M : :class:`scipy.sparse.csc.csc_matrix` or :class:`scipy.sparse.csr.csr_matrix`
        Matrix to normalize.
    outfmt : {'csc', 'csr'}
        Output format for the normalized matrix.

    Returns
    -------
    M : :class:`scipy.sparse.csc.csc_matrix` or :class:`scipy.sparse.csr.csr_matrix`
        The *same* matrix (not a copy), normalized over its columns, in format
        `outfmt`.

    Raises
    ------
    ValueError
        If the output format is not recognized.

    """

    # If the matrix is CSR, convert to CSC.

    if M.getformat() == 'csr':
        M = M.tocsc()

    # Normalize on the columns.

    print 'Normalizing matrix on the columns...',
    num_lems = M.get_shape()[0]

    for i in xrange(num_lems):

        col_vals = M.data[M.indptr[i]:M.indptr[i + 1]].copy()
        M.data[M.indptr[i]:M.indptr[i + 1]] = col_vals / np.sum(col_vals)

    print 'OK'

    # Convert to outfmt if necessary.

    if outfmt == 'csr':
        M = M.tocsr()
    elif outfmt != 'csc':
        raise ValueError("Unrecognized matrix format: '{}'".format(outfmt))

    return M


def norm_l1(v):
    """Compute the :math:`l_1` norm of an array.

    The :math:`l_1` norm is defined as :math:`l_1(v) = \sum_i |v_i|`.

    """

    return np.sum(np.abs(v))


def matrix_eigen_solve(M, v0, max_it, tol, damp_v=0.0, d=1.0):
    """Solve the :math:`v = M \cdot v` eigenproblem using the
    `Power Iteration <http://en.wikipedia.org/wiki/Power_iteration>`_ algorithm.

    This will only work on a stochastic matrix, since there is no vector
    renormalization (it creates precision problems). Note that to avoid
    oscillation in the algorithm, each iteration consists in fact of a random
    number (1-9) of iterations, and the new vector is the mean of the old one
    and the new computed value (see code).

    Parameters
    ----------
    M : matrix_like
        Matrix for the eigenproblem, preferably in CSR format (computation will
        be faster). It must implement the ``dot()`` method.
    v0 : :class:`numpy.ndarray`
        Starting vector for the iteration; should be normalized.
    max_it : int
        Maximum number of iterations to be performed.
    tol : float
        Requested relative precision.
    damp_v : :class:`numpy.ndarray`, optional
        Damping vector (normalized); defaults to a vector of zeros.
    d : float
        Damping factor; defaults to 1 (no damping).

    Returns
    -------
    v : :class:`numpy.ndarray`
        The final eigenvector.
    nit : int
        The number of iterations performed.
    prec : float
        The final relative precision.

    """

    # Initialize

    v = d * M.dot(v0) + (1 - d) * damp_v
    nit = 0

    # Loop until we reach the tolerance, or do too many iterations.

    while (norm_l1((d * M.dot(v) + (1 - d) * damp_v) - v) >= tol and
           nit < max_it):

        # Do the iteration calculus. The mean v = (v + ...) is to avoid
        # oscillations in the iterations.

        for i in range(random.randint(1, 10)):
            v = (v + (d * M.dot(v) + (1 - d) * damp_v)) / 2

        nit += 1

    # Return convergence information with the solution.

    return (v, nit, norm_l1((d * M.dot(v) + (1 - d) * damp_v) - v))
