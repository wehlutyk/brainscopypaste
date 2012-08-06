#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the lemmas in Wordnet, and save the scores
dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


if __name__ == '__main__':

    # Load or compute the PR scores for 'all'

    picklefile_all = st.wordnet_PR_scores_pickle.format('all')
    try:
        st.check_file(picklefile_all)
    except Exception:

        print
        print "The PR score data for 'all' already exists, loading that data."
        PR_scores_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing PR scores for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        PR_scores_all = wnt.build_wn_PR_scores('all')

        print "*** Saving the PR scores to '" + picklefile_all + "'...",
        ps.save(PR_scores_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.memetracker_subst_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wordnet_PR_scores_pickle.format(p)

        try:
            st.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the PR scores.

        print
        print ("*** Truncating the PR scores for 'all' to "
               'POS={} ***').format(p)
        PR_scores = wnt.truncate_wn_features(PR_scores_all, p)

        # And save them.

        print "*** Saving the PR scores to '" + picklefile + "'...",
        ps.save(PR_scores, picklefile)
        print 'OK'
