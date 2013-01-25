#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the out-degree for the lemmas in FreeAssociation, and save
the scores dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.fa as l_fa
import datainterface.fs as di_fs
import settings as st

if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.fa_norms_outdegrees_pickle
    di_fs.check_file(picklefile)

    # Compute the BCs.

    print '*** Computing outdegrees from the Free Association norms ***'
    outdegrees = l_fa.build_fa_outdegrees()
    print

    # And save them to pickle.

    print "*** Saving the outdegrees to '" + picklefile + "'...",
    ps.save(outdegrees, picklefile)
    print 'OK'
