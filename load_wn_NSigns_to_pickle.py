#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the mean number of meanings for the lemmas in WordNet,
and save the scores dict to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the NSins for 'all'

    picklefile_all = st.wn_NSigns_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The NSigns data for 'all' already exists, loading that data."
        NSigns_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing NSigns for all the lemmas in WordNet '
               "(POS = 'all') ***")
        NSigns_all = l_wn.build_wn_NSigns()

        print "*** Saving the NSigns to '" + picklefile_all + "'...",
        ps.save(NSigns_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.mt_mining_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wn_NSigns_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the NSigns.

        print
        print ("*** Truncating the NSigns for 'all' to POS={} ***").format(p)
        NSigns = l_wn.truncate_wn_features(NSigns_all, p)

        # And save them.

        print "*** Saving the NSigns to '" + picklefile + "'...",
        ps.save(NSigns, picklefile)
        print 'OK'
