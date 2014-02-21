#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the word frequencies from the MemeTracker dataset and store
the scores dict to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.mt as l_mt
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Does the destionation file already exit?

    picklefile = st.mt_frequencies_pickle
    di_fs.check_file(picklefile)

    # Compute the word frequencies
    print '*** Computing the word frequencies from MemeTracker ***'
    freqs = l_mt.compute_word_frequencies()
    print

    # And save them to pickle

    print "*** Saving the frequencies to '" + picklefile + "'...",
    ps.save(freqs, picklefile)
    print 'OK'
