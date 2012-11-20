#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the Free Association norms, and save that
to pickle."""


import linguistics.fa as l_fa
import datainterface.picklesaver as ps
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.fa_norms_PR_scores_pickle
    di_fs.check_file(picklefile)

    # Load the norms.

    print 'Loading Free Association norms from pickle...',
    norms = ps.load(st.fa_norms_pickle)
    print 'OK'

    # Compute the PageRank scores.

    print '*** Computing PageRank scores from the Free Association norms ***'
    PRscores = l_fa.build_fa_PR_scores(norms)
    print

    # And save them to pickle.

    print "*** Saving the scores to '" + picklefile + "'...",
    ps.save(PRscores, picklefile)
    print 'OK'
