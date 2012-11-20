#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load Free Association norms from files into pickle."""


import datainterface.fa as di_fa
import datainterface.picklesaver as ps
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # The destination file; check it doesn't already exist

    picklefile = st.freeassociation_norms_pickle
    di_fs.check_file(picklefile)

    # Load the norms.

    print 'Loading all the Free Association norms...',
    fa = di_fa.FreeAssociationNorms(st.freeassociation_norms_all)
    fa.load_norms()
    print 'OK'

    # And save them to pickle.

    print 'Saving data to pickle...',
    ps.save(fa.norms, picklefile)
    print 'OK'
