#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the substitutions (levenshtein_word distance = 1) in the MemeTracker dataset.

TODO: this script needs more commenting.

"""


# Imports
from __future__ import division
import datainterface.picklesaver as ps
import settings as st


# Code
n_timebags = 3
ball_radius = 1

# Load the clusters and the PageRank scores
clusters = ps.load(st.memetracker_full)
PR = ps.load(st.wordnet_PR_pickle)

ratios = []
for cl in clusters:
    tbgs = cl.build_timebags(n_timebags)
    for i in xrange(n_timebags-1):
        ball_strings = tbgs[i+1].levenshtein_word_closedball(tbgs[i].max_freq_string, ball_radius)
        for s in ball_strings:
            # TODO: Do stuff here
            pass

