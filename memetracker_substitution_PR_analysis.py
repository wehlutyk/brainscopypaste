#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes (levenshtein_word distance = 1) in the MemeTracker dataset.

TODO: this script needs more commenting.

"""


# Imports
from __future__ import division
from nltk import word_tokenize
import numpy as np
import datainterface.picklesaver as ps
import settings as st


# Code
n_timebags = 3
bag_transitions = [(0, 2)]
sphere_radius = 1
pickle_transitionranks = st.memetracker_PR_transitionranks_pickle
pickle_nonlemmas = st.memetracker_PR_nonlemmas_pickle


# Check that the destinations don't already exist
st.check_file(pickle_transitionranks)
st.check_file(pickle_nonlemmas)


# Load the clusters and the PageRank scores
print 'Loading cluster and PageRank data...',
clusters = ps.load(st.memetracker_full_pickle)
PR = ps.load(st.wordnet_PR_pickle)
print 'OK'


# Stuff for printing progress information
n_clusters = len(clusters)
info_step = int(round(n_clusters / 100))


# Do the actual computing
print 'Doing PageRank substitution analysis:'
transitionranks = []
nonlemmas = []
progress = 0
for cl in clusters.itervalues():
    # Progress info
    progress += 1
    if progress % info_step == 0:
        print '  {} % ({} / {} clusters)'.format(int(round(100*progress/n_clusters)), progress, n_clusters)
    
    # Build the TimeBags for that Cluster
    tbgs = cl.build_timebags(n_timebags)
    for i, j in bag_transitions:
        # Get the highest freq string in a TimeBag, as well as its "daughter" strings (hamming_word distance = 1)
        smax = tbgs[i].max_freq_string
        ball_strings = [ tbgs[j].strings[k] for k in tbgs[j].hamming_word_sphere(smax, sphere_radius)]
        for s in ball_strings:
            # Find the word that was changed
            t_s = word_tokenize(s)
            t_smax = word_tokenize(smax)
            idx = np.where([w1 != w2 for (w1,w2) in zip(t_s, t_smax)])[0]
            # See if the concerned words are in the PR scores
            try:
                # If so, store the two PR ranks (the [0] are to take out the unnecessary 1-dimension of PR[...])
                transitionranks.append([ PR[t_smax[idx]][0], PR[t_s[idx]][0] ])
            except KeyError:
                # If not, keep track of what we left out
                nonlemmas.append({'cl_id': cl.id, 't_s': t_s, 't_smax': t_smax, 'idx': idx})


# And save the data
print 'Done. Saving data...',
ps.save(np.array(transitionranks), pickle_transitionranks)
ps.save(nonlemmas, pickle_nonlemmas)
print 'OK'
