#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the clusterization coefficients for the lemmas in Wordnet, and save
the scores dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


if __name__ == '__main__':

    # Load or compute the CCs for 'all'

    picklefile_all = st.wordnet_CCs_pickle.format('all')
    try:
        st.check_file(picklefile_all)
    except Exception:

        print
        print "The CC data for 'all' already exists, loading that data."
        CCs_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing CCs for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        CCs_all = wnt.build_wn_CCs('all')

        print "*** Saving the CCs to '" + picklefile_all + "'...",
        ps.save(CCs_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.memetracker_subst_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wordnet_CCs_pickle.format(p)

        try:
            st.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the CCs.

        print
        print ("*** Truncating the CCs for 'all' to POS={} ***").format(p)
        CCs = wnt.truncate_wn_features(CCs_all, p)

        # And save them.

        print "*** Saving the CCs to '" + picklefile + "'...",
        ps.save(CCs, picklefile)
        print 'OK'
