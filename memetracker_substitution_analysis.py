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
import argparse
import textwrap
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import numpy as np
import datainterface.picklesaver as ps
import settings as st


# Code

# Create the arguments parser, to get arguments from the command line
parser = argparse.ArgumentParser(description=textwrap.dedent('''
                                             Analyze the 1-word changes \
                                             (hamming_word-distance == 1) in the MemeTracker dataset.
                                             '''))
parser.add_argument('--framing', action='store', nargs=1, \
                    required=True, help=textwrap.dedent('''
                                        1: analyze framed clusters ; \
                                        0: analyse non-framed clusters.
                                        '''))
parser.add_argument('--lemmatizing', action='store', nargs=1, \
                    required=True, help=textwrap.dedent("""
                                        1: lemmatize words before searching \
                                        for them in the features lists ; 0: don't lemmatize them.
                                        """))
parser.add_argument('--synonyms', action='store', nargs=1, \
                    required=True, help=textwrap.dedent("""
                                        1: compare only synonym words (i.e. words that both have a \
                                        lemma in the same synset ; 0: compare also non-synonyms.
                                        """))
parser.add_argument('--ntimebags', action='store', nargs=1, required=True, \
                    help='Number of timebags to cut the clusters into')
parser.add_argument('transitions', action='store', nargs='+', \
                    help=textwrap.dedent("""
                         Space-separated list of transitions between timebags 
                         that are to be examined, in format 'n1-n2' where n1 and n2 are the indices of 
                         the timebags (starting at 0) ; e.g. '0-1 1-2'.
                         """))


# Get the actual arguments
args = parser.parse_args()
framing = int(args.framing[0])
lemmatizing = int(args.lemmatizing[0])
synonyms_only = int(args.synonyms[0])
n_timebags = int(args.ntimebags[0])
bag_transitions = [ (int(s.split('-')[0]), int(s.split('-')[1])) for s in args.transitions ]


# A few checks on the arguments:
# Check that the transitions are possible, given the number of timebags
all_idx = [ i for tr in bag_transitions for i in tr ]
if max(all_idx) >= n_timebags or min(all_idx) < 0:
    raise Exception('Wrong bag transitions, according to the number of timebags requested')
# Check the other arguments
if framing != 0 and framing != 1:
    raise Exception('Wrong value for --framing. Expected 1 or 0.')
if lemmatizing != 0 and lemmatizing != 1:
    raise Exception('Wrong value for --lemmatizing. Expected 1 or 0.')
if synonyms_only != 0 and synonyms_only != 1:
    raise Exception('Wrong value for --synonyms. Expected 1 or 0.')


# Radius of the sphere of strings around a given string
sphere_radius = 1

# Filenames for saving the data, with a prefix depending on the options
file_prefix = ''
if framing == 0:
    file_prefix += 'N'
file_prefix += 'F_'
if lemmatizing == 0:
    file_prefix += 'N'
file_prefix += 'L_'
if synonyms_only == 0:
    file_prefix += 'N'
file_prefix += 'S_'
file_prefix += str(n_timebags) + '_'
for (i, j) in bag_transitions:
    file_prefix += '{}-{}_'.format(i, j)

pickle_transitionPRscores = st.memetracker_subst_transitionPRscores_pickle.format(file_prefix)
pickle_transitiondegrees = st.memetracker_subst_transitiondegrees_pickle.format(file_prefix)
pickle_nonlemmas = st.memetracker_subst_nonlemmas_pickle.format(file_prefix)


# Check that the destinations don't already exist
st.check_file(pickle_transitionPRscores)
st.check_file(pickle_transitiondegrees)
st.check_file(pickle_nonlemmas)


# Print some info, and load the clusters and the PageRank scores
print 'Doing analysis with the following parameters:'
print '  framing = {}'.format(framing)
print '  lemmatizing = {}'.format(lemmatizing)
print '  synonyms = {}'.format(synonyms_only)
print '  n_timebags = {}'.format(n_timebags)
print '  transitions = {}'.format(bag_transitions)
print
print 'Loading cluster, PageRank, and degree data...',
if framing == 1:
    clusters = ps.load(st.memetracker_full_framed_pickle)
else:
    clusters = ps.load(st.memetracker_full_pickle)
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
            if lemmatizing == 1:
                # Lemmatize the words
                lem1 = lemmatizer.lemmatize(t_smax[idx])
                lem2 = lemmatizer.lemmatize(t_s[idx])
            else:
                # Don't lemmatize words
                lem1 = t_smax[idx]
                lem2 = t_s[idx]
            if synonyms_only == 1:
                # See if the words have a common synset, i.e. are they synonyms.
                # If not, break to next item in the loop
                if len(set(wn.synsets(lem1)).intersection(set(wn.synsets(lem2)))) == 0:
                    break
            # See if the concerned words are in the feature lists
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
