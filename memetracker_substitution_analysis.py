#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes (hamming_word-distance == 1) in the MemeTracker dataset.

This script looks at features of words that are substituted through time in the MemeTracker Clusters. The
features are the Wordnet PageRank scores of the words, and their degree in the Wordnet graph.

Details:
  The script takes each Cluster, splits it into a number of TimeBags, then looks at the transitions
  between TimeBags defined by the 'bag_transitions' variable: for each transition (e.g. TimeBag #0 to TimeBag #2),
  it takes the highest frequency string in the first TimeBag, gets all strings in the second TimeBag which are at
  hamming_word-distance == 1, and stores the features of the substituted word and the new word if they happen to be
  synonyms. If any one of those words is not referenced in the features (e.g. is not the PR scores list), it takes
  note of it (in the 'nonlemmas' variable). It then saves all the data to pickle files.

The output is as follows (see settings.py for the full filenames):
  * one file containing the PR scores of (substituted word, new word) couples (which is a Nx2 numpy array)
  * one file containing the degrees of (substituted word, new word) couples (again a Nx2 numpy array)
  * one file containing a list of dicts with data about the words that didn't have associated features
    (the data stored is: cluster id ('cl_id'), tokenized start string ('t_smax'), tokenized end string ('t_s')
    and index of the changed word ('idx')).

"""


# Imports
from __future__ import division
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import numpy as np
import datainterface.picklesaver as ps
import settings as st


# Code
n_timebags = 2
bag_transitions = [(0, 1)]
sphere_radius = 1
pickle_transitionPRscores = st.memetracker_subst_transitionPRscores_pickle
pickle_transitiondegrees = st.memetracker_subst_transitiondegrees_pickle
pickle_nonlemmas = st.memetracker_subst_nonlemmas_pickle


# Check that the destinations don't already exist
st.check_file(pickle_transitionPRscores)
st.check_file(pickle_nonlemmas)


# Load the clusters and the PageRank scores
print 'Loading cluster, PageRank, and degree data...',
#clusters = ps.load(st.memetracker_full_pickle)
clusters = ps.load(st.memetracker_full_framed_pickle)
PR = ps.load(st.wordnet_PR_scores_pickle)
degrees = ps.load(st.wordnet_degrees_pickle)
print 'OK'


# Stuff for printing progress information
n_clusters = len(clusters)
info_step = max(int(round(n_clusters / 100)), 1)


# Do the actual computing
print 'Doing substitution analysis:'
transitionPRscores = []
transitiondegrees = []
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
            # Lemmatize the words
            lem1 = lemmatizer.lemmatize(t_smax[idx])
            lem2 = lemmatizer.lemmatize(t_s[idx])
#            # Don't lemmatize words
#            lem1 = t_smax[idx]
#            lem2 = t_s[idx]
            # See if the words have a common synset, i.e. are they synonyms
            if len(set(wn.synsets(lem1)).intersection(set(wn.synsets(lem2)))) > 0:
                # See if the concerned words are in the PR scores
                try:
                    # If so, store the features
                    transitionPRscores.append([ PR[lem1], PR[lem2] ])
                    transitiondegrees.append([ degrees[lem1], degrees[lem2] ])
                except KeyError:
                    # If not, keep track of what we left out
                    nonlemmas.append({'cl_id': cl.id, 't_s': t_s, 't_smax': t_smax, 'idx': idx})


# And save the data
print 'Done. Saving data...',
ps.save(np.array(transitionPRscores), pickle_transitionPRscores)
ps.save(np.array(transitiondegrees), pickle_transitiondegrees)
ps.save(nonlemmas, pickle_nonlemmas)
print 'OK'
