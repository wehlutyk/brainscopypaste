#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the clustering coefficients for the lemmas in FreeAssociation,
and save the scores dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.fa as l_fa
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.fa_norms_CCs_pickle
    di_fs.check_file(picklefile)

    # Compute the BCs.

    print '*** Computing CCs from the Free Association norms ***'
    CCs = l_fa.build_fa_CCs()
    print

    # And save them to pickle.

    print "*** Saving the CCs to '" + picklefile + "'...",
    ps.save(CCs, picklefile)
    print 'OK'
