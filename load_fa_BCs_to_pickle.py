#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the betweenness coefficients for the lemmas in FreeAssociation, and save
the scores dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.fa as l_fa
import datainterface.fs as di_fs
import settings as st

if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.fa_norms_BCs_pickle
    di_fs.check_file(picklefile)

    # Load the norms.

    print 'Loading Free Association norms from pickle...',
    norms = ps.load(st.fa_norms_pickle)
    print 'OK'

    # Compute the BCs.

    print '*** Computing BCs from the Free Association norms ***'
    BCs = l_fa.build_fa_BCs(norms)
    print

    # And save them to pickle.

    print "*** Saving the BCs to '" + picklefile + "'...",
    ps.save(BCs, picklefile)
    print 'OK'
