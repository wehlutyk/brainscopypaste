#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the degrees for the lemmas in Wordnet, and save the scores dict to
a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the degrees for 'all'

    picklefile_all = st.wordnet_degrees_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The degree data for 'all' already exists, loading that data."
        degrees_all = ps.load(picklefile_all)

    else:

        print
        print ('*** Computing degrees for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        degrees_all = l_wn.build_wn_degrees('all')

        print "*** Saving the degrees to '" + picklefile_all + "'...",
        ps.save(degrees_all, picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.memetracker_subst_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wordnet_degrees_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the degrees.

        print
        print ("*** Truncating the degrees for 'all' to POS={} ***").format(p)
        degrees = l_wn.truncate_wn_features(degrees_all, p)

        # And save them.

        print "*** Saving the degrees to '" + picklefile + "'...",
        ps.save(degrees, picklefile)
        print 'OK'
