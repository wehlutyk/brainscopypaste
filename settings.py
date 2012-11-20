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

from datainterface.fs import check_folder


##############################################################################
# DATA ROOT #
#############
#
# Root folder for all the data. If we do this properly, this could be the only
# setting to change between computers :-). This could be changed to
# '~/Code/cogmaster-stage/data', or even better '../data'.
# But we should check that it works...

data_root = '/home/sebastien/Code/Research/WebQuotes/data'
if not os.path.exists(data_root):
    os.makedirs(data_root)


###############################################################################
# WORDNET DATA #
################
#
# Root folder for Wordnet scores data, relative to data_root

wordnet_root_rel = 'Wordnet'
wordnet_root = os.path.join(data_root, wordnet_root_rel)
check_folder(wordnet_root)


# Pickle file for the Wordnet PageRank scores, relative to wordnet root.

wordnet_PR_scores_pickle_rel = 'wordnet_PR_scores_{}.pickle'
wordnet_PR_scores_pickle = os.path.join(wordnet_root,
                                        wordnet_PR_scores_pickle_rel)


# Pickle file for the Wordnet degrees, relative to wordnet root.

wordnet_degrees_pickle_rel = 'wordnet_degrees_{}.pickle'
wordnet_degrees_pickle = os.path.join(wordnet_root,
                                      wordnet_degrees_pickle_rel)


# Pickle file for the Wordnet clusterization coefficients, relative to wordnet
# root.

wordnet_CCs_pickle_rel = 'wordnet_CCs_{}.pickle'
wordnet_CCs_pickle = os.path.join(wordnet_root,
                                 wordnet_CCs_pickle_rel)


# Pickle file for the Wordnet betweenness, relative to wordnet root.

wordnet_BCs_pickle_rel = 'wordnet_BCs_{}.pickle'
wordnet_BCs_pickle = os.path.join(wordnet_root,
                                  wordnet_BCs_pickle_rel)


# Pickle file for the Wordnet Number of significations, relative to wordnet
# root

wordnet_NSigns_pickle_rel = 'wordnet_NSigns_{}.pickle'
wordnet_NSigns_pickle = os.path.join(wordnet_root,
                                     wordnet_NSigns_pickle_rel)


# Pickle file for the Wordnet Mean Number of Synonyms, relative to wordnet root

wordnet_MNSyns_pickle_rel = 'wordnet_MNSyns_{}.pickle'
wordnet_MNSyns_pickle = os.path.join(wordnet_root,
                                     wordnet_MNSyns_pickle_rel)


##############################################################################
# CMU PRONOUNCIATION DATA #
###########################
#
# Folder for the CMU Pronouciation data, relative to data_root

cmu_root_rel = 'CMU'
cmu_root = os.path.join(data_root, cmu_root_rel)
check_folder(cmu_root)


# Pickle file for the CMU number of syllables, relative to cmu_root

cmu_MNsyllables_pickle_rel = 'cmu_MNsyllables.pickle'
cmu_MNsyllables_pickle = os.path.join(cmu_root, cmu_MNsyllables_pickle_rel)


# Pickle file for the CMU number of phonemes, relative to cmu_root

cmu_MNphonemes_pickle_rel = 'cmu_MNphonemes.pickle'
cmu_MNphonemes_pickle = os.path.join(cmu_root, cmu_MNphonemes_pickle_rel)


##############################################################################
# AGE-OF-ACQUISITION DATA #
###########################
#
# Folder for the AoA data, relative to data_root

aoa_root_rel = 'AoA'
aoa_root = os.path.join(data_root, aoa_root_rel)
check_folder(aoa_root)


# Source csv file for the Kuperman AoA data, relative to aoa_root

aoa_Kuperman_csv_rel = 'Kuperman-BRM-data-2012.csv'
aoa_Kuperman_csv = os.path.join(aoa_root, aoa_Kuperman_csv_rel)


# Pickle file for the AoA Kuperman data, relative to aoa_root

aoa_Kuperman_pickle_rel = 'aoa_Kuperman.pickle'
aoa_Kuperman_pickle = os.path.join(aoa_root, aoa_Kuperman_pickle_rel)


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


#############################################################################
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
memetracker_full_filtered_pickle = memetracker_full + '_filtered.pickle'
memetracker_full_ff_pickle = memetracker_full + '_ff.pickle'


# File for a subset of the MemeTracker dataset for testing algorithms before a
# full-blown run, relative to memetracker_root.

memetracker_test_rel = 'clust-cropped-50000.txt'

memetracker_test = os.path.join(memetracker_root, memetracker_test_rel)
memetracker_test_pickle = memetracker_test + '.pickle'
memetracker_test_framed_pickle = memetracker_test + '_framed.pickle'
memetracker_test_filtered_pickle = memetracker_test + '_filtered.pickle'
memetracker_test_ff_pickle = memetracker_test + '_ff.pickle'


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


# List of available features.

memetracker_subst_features = {'wn': {'PR_scores': wordnet_PR_scores_pickle,
                                     'degrees': wordnet_degrees_pickle,
                                     'CCs': wordnet_CCs_pickle,
                                     'BCs': wordnet_BCs_pickle,
                                     'NSigns': wordnet_NSigns_pickle,
                                     'MNSyns': wordnet_MNSyns_pickle},
                              'fa': {'PR_scores': freeassociation_norms_PR_scores_pickle},
                              'cmu': {'MNsyllables': cmu_MNsyllables_pickle,
                                      'MNphonemes': cmu_MNphonemes_pickle},
                              'aoa': {'Kuperman': aoa_Kuperman_pickle}
                              }


# For each feature, boolean telling us if we should lemmatize or not

memetracker_subst_features_lem = {'wn': {'PR_scores': True,
                                     'degrees': True,
                                     'CCs': True,
                                     'BCs': True,
                                     'NSigns': True,
                                     'MNSyns': True},
                              'fa': {'PR_scores': True},
                              'cmu': {'MNsyllables': False,
                                      'MNphonemes': False},
                              'aoa': {'Kuperman': True}
                              }


# List of mining models which are based on slicing the clusters into a given
# n_timebags number of timebags

memetracker_mining_fixedslicing_models = ['slidetbgs', 'tbgs', 'cumtbgs', 'root']

# Pickle files for the MemeTracker substitution analysis, relative to
# memetracker_subst_root.

memetracker_subst_results_pickle_rel = '{}results.pickle'
memetracker_subst_results_pickle = os.path.join(memetracker_subst_root,
                                                memetracker_subst_results_pickle_rel)


# List of available POS tags, taken as options for the analysis scripts.

memetracker_subst_POSs = ['a', 'n', 'v', 'r', 'all']


##############################################################################
# TREETAGGER SETTINGS #
#######################
#
# Folder where the treetagger executables and libs live.

treetagger_TAGDIR = '/usr/share/treetagger'


##############################################################################
# REDIS SETTINGS #
##################
#
# Prefixes for storing data from the Memetracker dataset.

redis_mt_pref = 'memetracker:'
redis_mt_clusters_pref = redis_mt_pref + 'clusters:'
redis_mt_clusters_framed_pref = redis_mt_pref + 'clusters-framed:'
redis_mt_clusters_filtered_pref = redis_mt_pref + 'clusters-filtered:'
redis_mt_clusters_ff_pref = redis_mt_pref + 'clusters-ff:'
