#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Global settings for files and folders, for the scripts to run."""


import os


# Two routines for checking if folders and files exist.

def check_folder(folder):
    """Check if folder exists; if not, create it and notify the user."""
    if not os.path.exists(folder):
        print "*** Settings: '" + folder + "' does not exist. Creating it."
        os.makedirs(folder)


def check_file(filename):
    """Check if filename already exists; if it does, raise an exception."""
    if os.path.exists(filename):
        
        raise Exception(("File '" + filename + "' already exists! You should "
                         "sort this out first: I'm not going to overwrite "
                         'it. Aborting.'))


# Root folder for all the data. If we do this properly, this could be the only
# setting to change between computers :-). This could be changed to
# '~/Code/cogmaster-stage/data', or even better '../data'.
# But we should check that it works...

data_root = '/home/sebastien/Code/cogmaster-stage/data'

if not os.path.exists(data_root):
    os.makedirs(data_root)


# Folder for MemeTracker data, relative to data_root.

memetracker_root_rel = 'MemeTracker'

memetracker_root = os.path.join(data_root, memetracker_root_rel)
check_folder(memetracker_root)


# File for the complete MemeTracker dataset, relative to memetracker_root.

memetracker_full_rel = 'clust-qt08080902w3mfq5.txt'

memetracker_full = os.path.join(memetracker_root, memetracker_full_rel)
memetracker_full_pickle = memetracker_full + '.pickle'
memetracker_full_framed_pickle = memetracker_full + '_framed.pickle'


# File for a subset of the MemeTracker dataset for testing algorithms before a
# full-blown run, relative to memetracker_root.

memetracker_test_rel = 'clust-cropped-50000.txt'

memetracker_test = os.path.join(memetracker_root, memetracker_test_rel)
memetracker_test_pickle = memetracker_test + '.pickle'
memetracker_test_framed_pickle = memetracker_test + '_framed.pickle'


# Folder for files concerning the MemeTracker substitution PageRank analysis.

memetracker_subst_root_rel = 'subst_analysis'

memetracker_subst_root = os.path.join(memetracker_root,
                                      memetracker_subst_root_rel)
check_folder(memetracker_subst_root)


# Pickle files for the MemeTracker substitution analysis.

memetracker_subst_transitionPRscores_pickle_rel = \
    '{}transitionPRscores.pickle'
memetracker_subst_transitiondegrees_pickle_rel = '{}transitiondegrees.pickle'
memetracker_subst_nonlemmas_pickle_rel = '{}nonlemmas.pickle'

memetracker_subst_transitionPRscores_pickle = os.path.join(
    memetracker_subst_root, memetracker_subst_transitionPRscores_pickle_rel)
memetracker_subst_transitiondegrees_pickle = os.path.join(
    memetracker_subst_root, memetracker_subst_transitiondegrees_pickle_rel)


# Pickle file for the Wordnet PageRank scores, relative to data_root.

wordnet_PR_scores_pickle_rel = 'wordnet_PR_scores.pickle'

wordnet_PR_scores_pickle = os.path.join(data_root,
                                        wordnet_PR_scores_pickle_rel)


# Pickle file for the Wordnet degrees, relative to data root.

wordnet_degrees_pickle_rel = 'wordnet_degrees.pickle'

wordnet_degrees_pickle = os.path.join(data_root, wordnet_degrees_pickle_rel)


# TreeTagger settings

treetagger_TAGDIR = '/usr/share/treetagger'
