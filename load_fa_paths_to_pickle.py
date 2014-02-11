#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute all the shortest path lengths in the Free Association network,
their distribution, and save that to pickle."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.fa as l_fa
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the BCs for 'all'

    picklefile = st.fa_lengths_pickle

    di_fs.check_file(picklefile)

    print
    print '*** Computing FA path lengths ***'
    lengths_detail = l_fa.build_fa_paths()

    print '*** Computing FA path length distribution ***'
    distribution = l_fa.build_fa_paths_distribution(lengths_detail)

    print "*** Saving the FA path length distribution to '" + \
        picklefile + "'...",
    ps.save(distribution, picklefile)
    print 'OK'
