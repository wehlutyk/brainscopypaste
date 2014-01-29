#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the lemmas in Wordnet, and save the scores
dict to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the PR scores for 'all'

    picklefile_all = st.wn_PR_scores_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The PR score data for 'all' already exists, loading that data."
        PR_scores_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing PR scores for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        PR_scores_all = l_wn.build_wn_PR_scores('all')

        print "*** Saving the PR scores to '" + picklefile_all + "'...",
        ps.save(PR_scores_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.mt_mining_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wn_PR_scores_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the PR scores.

        print
        print ("*** Truncating the PR scores for 'all' to "
               'POS={} ***').format(p)
        PR_scores = l_wn.truncate_wn_features(PR_scores_all, p)

        # And save them.

        print "*** Saving the PR scores to '" + picklefile + "'...",
        ps.save(PR_scores, picklefile)
        print 'OK'
