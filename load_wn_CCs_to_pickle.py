#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the clustering coefficients for the lemmas in Wordnet, and save
the scores dict to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the CCs for 'all'

    picklefile_all = st.wn_CCs_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The CC data for 'all' already exists, loading that data."
        CCs_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing CCs for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        CCs_all = l_wn.build_wn_CCs('all')

        print "*** Saving the CCs to '" + picklefile_all + "'...",
        ps.save(CCs_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.mt_mining_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wn_CCs_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the CCs.

        print
        print ("*** Truncating the CCs for 'all' to POS={} ***").format(p)
        CCs = l_wn.truncate_wn_features(CCs_all, p)

        # And save them.

        print "*** Saving the CCs to '" + picklefile + "'...",
        ps.save(CCs, picklefile)
        print 'OK'
