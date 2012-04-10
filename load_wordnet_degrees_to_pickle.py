#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the degrees for the lemmas in Wordnet, and save the scores dict to a pickle file."""


# Imports
import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


# Code
picklefile = st.wordnet_degrees_pickle

# Check that the destination doesn't already exist
st.check_file(picklefile)

# Compute the PR scores
print '*** Computing degrees for the lemmas in Wordnet:'
degrees = wnt.build_wn_degrees()

# And save them
print "*** Saving the degrees to '" + picklefile + "'...",
ps.save(degrees, picklefile)
print 'OK'
