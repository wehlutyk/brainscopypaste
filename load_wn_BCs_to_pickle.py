#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the clusterization coefficients for the lemmas in Wordnet, and save
the scores dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the BCs for 'all'

    picklefile_all = st.wordnet_BCs_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The BC data for 'all' already exists, loading that data."
        BCs_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing BCs for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        BCs_all = l_wn.build_wn_BCs('all')

        print "*** Saving the BCs to '" + picklefile_all + "'...",
        ps.save(BCs_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.memetracker_subst_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wordnet_BCs_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the BCs.

        print
        print ("*** Truncating the BCs for 'all' to POS={} ***").format(p)
        BCs = l_wn.truncate_wn_features(BCs_all, p)

        # And save them.

        print "*** Saving the BCs to '" + picklefile + "'...",
        ps.save(BCs, picklefile)
        print 'OK'
