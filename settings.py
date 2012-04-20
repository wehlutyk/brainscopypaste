#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Global settings for files and folders, for the scripts to run.

Sections:
  * Utilities: check if files or folders are present
  * Data root: root folder for all data
  * Memetracker data: files to load from and save to for raw Memetracker data
  * Memetracker substitution analysis: files to save to for the Memetracker
                                       substitution analysis
  * Treetagger settings: folder where the treetagger executables and libs live
  * Wordnet data: files to save to for Wordnet network data
  * Free Association norms data: files to load from and save to for Free
                                 Association norms network data
  * Redis settings: prefixes to store data in the Redis key-value store

"""


import os


##############################################################################
# UTILITIES #
#############
#
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


##############################################################################
# DATA ROOT #
#############
#
# Root folder for all the data. If we do this properly, this could be the only
# setting to change between computers :-). This could be changed to
# '~/Code/cogmaster-stage/data', or even better '../data'.
# But we should check that it works...

data_root = '/home/sebastien/Code/cogmaster-stage/data'
if not os.path.exists(data_root):
    os.makedirs(data_root)


##############################################################################
# MEMETRACKER DATA #
####################
#
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


##############################################################################
# MEMETRACKER SUBSTITUTION ANALYSIS #
#####################################
#
# Folder for files concerning the MemeTracker substitution analysis, relative
# to memetracker_root.

memetracker_subst_root_rel = 'subst_analysis'
memetracker_subst_root = os.path.join(memetracker_root,
                                      memetracker_subst_root_rel)
check_folder(memetracker_subst_root)


# Pickle files for the MemeTracker substitution analysis, relative to
# memetracker_subst_root.

memetracker_subst_wn_PR_scores_pickle_rel = '{}wn_PR_scores.pickle'
memetracker_subst_wn_degrees_pickle_rel = '{}wn_degrees.pickle'
memetracker_subst_fa_PR_scores_pickle_rel = '{}fa_PR_scores.pickle'

memetracker_subst_wn_PR_scores_pickle = os.path.join(
    memetracker_subst_root, memetracker_subst_wn_PR_scores_pickle_rel)
memetracker_subst_wn_degrees_pickle = os.path.join(
    memetracker_subst_root, memetracker_subst_wn_degrees_pickle_rel)
memetracker_subst_fa_PR_scores_pickle = os.path.join(
    memetracker_subst_root, memetracker_subst_fa_PR_scores_pickle_rel)


##############################################################################
# TREETAGGER SETTINGS #
#######################
#
# Folder where the treetagger executables and libs live.

treetagger_TAGDIR = '/usr/share/treetagger'


##############################################################################
# WORDNET DATA #
################
#
# Pickle file for the Wordnet PageRank scores, relative to data_root.

wordnet_PR_scores_pickle_rel = 'wordnet_PR_scores.pickle'
wordnet_PR_scores_pickle = os.path.join(data_root,
                                        wordnet_PR_scores_pickle_rel)


# Pickle file for the Wordnet degrees, relative to data root.

wordnet_degrees_pickle_rel = 'wordnet_degrees.pickle'
wordnet_degrees_pickle = os.path.join(data_root, wordnet_degrees_pickle_rel)


##############################################################################
# FREE ASSOCIATION NORMS DATA #
###############################
#
# Folder for Free Association Norms data, relative to data_root.

freeassociation_root_rel = 'FreeAssociation'
freeassociation_root = os.path.join(data_root, freeassociation_root_rel)
check_folder(freeassociation_root)


# Files for raw Free Association data, relative to freeassociation_root.

freeassociation_norms_all_rel = ['Cue_Target_Pairs.A-B',
                                 'Cue_Target_Pairs.C',
                                 'Cue_Target_Pairs.D-F',
                                 'Cue_Target_Pairs.G-K',
                                 'Cue_Target_Pairs.L-O',
                                 'Cue_Target_Pairs.P-R',
                                 'Cue_Target_Pairs.S',
                                 'Cue_Target_Pairs.T-Z']
freeassociation_norms_all = [os.path.join(freeassociation_root, fn_rel) for
                             fn_rel in freeassociation_norms_all_rel]


# File for pickle Free Association data, relative to freeassociation_root.

freeassociation_norms_pickle_rel = 'norms.pickle'
freeassociation_norms_pickle = os.path.join(freeassociation_root,
                                            freeassociation_norms_pickle_rel)


# File for PageRank scores of the Free Association data, relative to
# freeassociation_root.

freeassociation_norms_PR_scores_pickle_rel = 'norms_PR_scores.pickle'
freeassociation_norms_PR_scores_pickle = \
    os.path.join(freeassociation_root,
                 freeassociation_norms_PR_scores_pickle_rel)


##############################################################################
# REDIS SETTINGS #
##################
#
# Prefixes for storing data from the Memetracker dataset.

redis_mt_pref = 'memetracker:'
redis_mt_clusters_pref = redis_mt_pref + 'clusters:'
redis_mt_clusters_framed_pref = redis_mt_pref + 'clusters-framed:'
