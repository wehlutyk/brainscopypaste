#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the lemmas in Wordnet, and save the scores dict to a pickle file."""


# Imports
import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


# Code
picklefile = st.wordnet_PR_scores_pickle

# Check that the destination doesn't already exist
st.check_file(picklefile)

# Compute the PR scores
print
print '*** Computing PageRank scores for the lemmas in Wordnet ***'
scores = wnt.build_wn_PR_scores()

# And save them
print
print "*** Saving the scores to '" + picklefile + "'...",
ps.save(scores, picklefile)
print 'OK'
