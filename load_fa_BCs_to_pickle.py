#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the betweenness centralities for the lemmas in FreeAssociation,
and save the scores dict to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.fa as l_fa
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.fa_norms_BCs_pickle
    di_fs.check_file(picklefile)

    # Compute the BCs.

    print '*** Computing BCs from the Free Association norms ***'
    BCs = l_fa.build_fa_BCs()
    print

    # And save them to pickle.

    print "*** Saving the BCs to '" + picklefile + "'...",
    ps.save(BCs, picklefile)
    print 'OK'
