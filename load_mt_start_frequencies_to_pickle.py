#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the word frequencies from the MemeTracker dataset in
start quotes involved in substitutions, and store the scores dict
to a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.mt as l_mt
import datainterface.fs as di_fs
from baseargs import BaseArgs
import settings as st


if __name__ == '__main__':

    # Substitution detection parameters to use

    params = {'ff': 'filtered',
              'model': 'tbgs',
              'POS': 'all',
              'substrings': False,
              'timebag_size': 5.0}
    bargs = BaseArgs(params)

    # Does the destionation file already exit?

    picklefile = st.mt_start_frequencies_pickle
    di_fs.check_file(picklefile)

    # Compute the word frequencies
    print ('*** Computing the word frequencies from start quotes '
           'invovled in substitutions in MemeTracker ***')
    start_freqs = l_mt.compute_word_frequencies_start_quotes(bargs)
    print

    # And save them to pickle

    print "*** Saving the start frequencies to '" + picklefile + "'...",
    ps.save(start_freqs, picklefile)
    print 'OK'
