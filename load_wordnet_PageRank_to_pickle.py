#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the lemmas in Wordnet, and save it to a pickle file."""


# Imports
import os
import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


# Code
picklefile = os.path.join(st.data_root, 'wordnet_PR_scores.pickle')

# Check that the destination doesn't already exist
if os.path.exists(picklefile):
    raise Exception("File '" + picklefile + "' already exists!")

# Compute the PR scores
print '*** Computing PageRank scores for the lemmas in Wordnet:'
scores = wnt.build_wn_PR_scores()

# And save them
print "*** Saving the scores to '" + picklefile + "'...",
ps.save(scores, picklefile)
print 'OK'
