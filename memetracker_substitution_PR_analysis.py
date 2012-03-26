#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes (hamming_word-distance == 1) in the MemeTracker dataset.

This script fetches the PR scores of words that are substituted through time in the MemeTracker Clusters.
It takes each Cluster, splits it into a number of TimeBags, then looks at the transitions between TimeBags
defined by the 'bag_transitions' variable: for each transition (e.g. TimeBag #0 to TimeBag #2), it takes
the highest frequency string in the first TimeBag, gets all strings in the second TimeBag which are at
hamming_word-distance == 1, and stores the scores of the substituted word and the new word. If any one of
those words is not referenced in the PR scores, it takes note of it (in the 'nonlemmas' variable). It then
saves all the data to pickle files. The output is two files: one containing the ranks of (substituted word, new word)
couples (which is a Nx2 numpy array), the other containing a list of dicts with data about the words that didn't
have PR scores (data stored is: cluster id ('cl_id'), tokenized start string ('t_smax'), tokenized end string ('t_s')
and index of the changed word ('idx')).

"""


# Imports
from __future__ import division
from nltk import word_tokenize
import numpy as np
from nltk.stem import WordNetLemmatizer
import datainterface.picklesaver as ps
import settings as st


# Code
n_timebags = 3
bag_transitions = [(0,1), (1, 2)]
sphere_radius = 1
pickle_transitionranks = st.memetracker_PR_transitionranks_pickle
pickle_nonlemmas = st.memetracker_PR_nonlemmas_pickle


# Check that the destinations don't already exist
st.check_file(pickle_transitionranks)
st.check_file(pickle_nonlemmas)


# Load the clusters and the PageRank scores
print 'Loading cluster and PageRank data...',
#clusters = ps.load(st.memetracker_full_pickle)
clusters = ps.load(st.memetracker_full_framed_pickle)
PR = ps.load(st.wordnet_PR_pickle)
print 'OK'


# Stuff for printing progress information
n_clusters = len(clusters)
info_step = int(round(n_clusters / 100))


# Do the actual computing
print 'Doing PageRank substitution analysis:'
transitionranks = []
nonlemmas = []
lemmatizer = WordNetLemmatizer()
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
            idx = np.where([w1 != w2 for (w1, w2) in zip(t_s, t_smax)])[0]
#            # Lemmatize the words
#            lem1 = lemmatizer.lemmatize(t_smax[idx])
#            lem2 = lemmatizer.lemmatize(t_s[idx])
            # Don't lemmatize words
            lem1 = t_smax[idx]
            lem2 = t_s[idx]
            # See if the concerned words are in the PR scores
            try:
                # If so, store the two PR ranks (the [0] are to take out the unnecessary 1-dimension of PR[...])
                transitionranks.append([ PR[lem1][0], PR[lem2][0] ])
            except KeyError:
                # If not, keep track of what we left out
                nonlemmas.append({'cl_id': cl.id, 't_s': t_s, 't_smax': t_smax, 'idx': idx})


# And save the data
print 'Done. Saving data...',
ps.save(np.array(transitionranks), pickle_transitionranks)
ps.save(nonlemmas, pickle_nonlemmas)
print 'OK'
