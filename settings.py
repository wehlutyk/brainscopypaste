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

wn_root_rel = 'Wordnet'
wn_root = os.path.join(data_root, wn_root_rel)
check_folder(wn_root)


# Pickle file for the Wordnet PageRank scores, relative to wordnet root.

wn_PR_scores_pickle_rel = 'wordnet_PR_scores_{}.pickle'
wn_PR_scores_pickle = os.path.join(wn_root,
                                   wn_PR_scores_pickle_rel)


# Pickle file for the Wordnet degrees, relative to wordnet root.

wn_degrees_pickle_rel = 'wordnet_degrees_{}.pickle'
wn_degrees_pickle = os.path.join(wn_root,
                                 wn_degrees_pickle_rel)


# Pickle file for the Wordnet clusterization coefficients, relative to wordnet
# root.

wn_CCs_pickle_rel = 'wordnet_CCs_{}.pickle'
wn_CCs_pickle = os.path.join(wn_root,
                             wn_CCs_pickle_rel)


# Pickle file for the Wordnet betweenness, relative to wordnet root.

wn_BCs_pickle_rel = 'wordnet_BCs_{}.pickle'
wn_BCs_pickle = os.path.join(wn_root,
                             wn_BCs_pickle_rel)


# Pickle file for the Wordnet Number of significations, relative to wordnet
# root

wn_NSigns_pickle_rel = 'wordnet_NSigns_{}.pickle'
wn_NSigns_pickle = os.path.join(wn_root,
                                wn_NSigns_pickle_rel)


# Pickle file for the Wordnet Mean Number of Synonyms, relative to wordnet root

wn_MNSyns_pickle_rel = 'wordnet_MNSyns_{}.pickle'
wn_MNSyns_pickle = os.path.join(wn_root,
                                wn_MNSyns_pickle_rel)


# Pickle file for the Wordnet path lengths distribution, relative to wordnet
# root

wn_lengths_pickle_rel = 'wordnet_lengths.pickle'
wn_lengths_pickle = os.path.join(wn_root,
                                 wn_lengths_pickle_rel)


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

fa_root_rel = 'FreeAssociation'
fa_root = os.path.join(data_root, fa_root_rel)
check_folder(fa_root)


# Files for raw Free Association data, relative to fa_root.

fa_norms_all_rel = ['Cue_Target_Pairs.A-B',
                    'Cue_Target_Pairs.C',
                    'Cue_Target_Pairs.D-F',
                    'Cue_Target_Pairs.G-K',
                    'Cue_Target_Pairs.L-O',
                    'Cue_Target_Pairs.P-R',
                    'Cue_Target_Pairs.S',
                    'Cue_Target_Pairs.T-Z']
fa_norms_all = [os.path.join(fa_root, fn_rel) for
                fn_rel in fa_norms_all_rel]


# File for pickle Free Association data, relative to fa_root.

fa_norms_pickle_rel = 'norms.pickle'
fa_norms_pickle = os.path.join(fa_root, fa_norms_pickle_rel)


# File for PageRank scores of the Free Association data, relative to
# fa_root.

fa_norms_PR_scores_pickle_rel = 'norms_PR_scores.pickle'
fa_norms_PR_scores_pickle = os.path.join(fa_root,
                                         fa_norms_PR_scores_pickle_rel)


#############################################################################
# MEMETRACKER DATA #
####################
#
# Folder for MemeTracker data, relative to data_root.

mt_root_rel = 'MemeTracker'
mt_root = os.path.join(data_root, mt_root_rel)
check_folder(mt_root)


# File for the complete MemeTracker dataset, relative to mt_root.

mt_full_rel = 'clust-qt08080902w3mfq5.txt'
mt_full = os.path.join(mt_root, mt_full_rel)
mt_full_pickle = mt_full + '.pickle'
mt_full_framed_pickle = mt_full + '_framed.pickle'
mt_full_filtered_pickle = mt_full + '_filtered.pickle'
mt_full_ff_pickle = mt_full + '_ff.pickle'


# File for a subset of the MemeTracker dataset for testing algorithms before a
# full-blown run, relative to mt_root.

mt_test_rel = 'clust-cropped-50000.txt'

mt_test = os.path.join(mt_root, mt_test_rel)
mt_test_pickle = mt_test + '.pickle'
mt_test_framed_pickle = mt_test + '_framed.pickle'
mt_test_filtered_pickle = mt_test + '_filtered.pickle'
mt_test_ff_pickle = mt_test + '_ff.pickle'


##############################################################################
# MEMETRACKER SUBSTITUTION MINING #
###################################
#
# Folder for files concerning the MemeTracker substitution mining, relative
# to mt_root.

mt_mining_root_rel = 'mining'
mt_mining_root = os.path.join(mt_root, mt_mining_root_rel)
check_folder(mt_mining_root)


# List of mining models which are based on slicing the clusters into a given
# n_timebags number of timebags

mt_mining_fixedslicing_models = ['slidetbgs', 'tbgs', 'cumtbgs', 'root']


# Pickle files for the MemeTracker substitution mining, relative to
# mt_mining_root.

mt_mining_substitutions_pickle_rel = '{}substitutions.pickle'
mt_mining_substitutions_pickle = os.path.join(mt_mining_root,
                                              mt_mining_substitutions_pickle_rel)


# List of available POS tags, taken as options for the analysis scripts.

mt_mining_POSs = ['a', 'n', 'v', 'r', 'all']


##############################################################################
# MEMETRACKER SUBSTITUTION ANALYSIS #
####################################
#
# List of available features, telling us which should use lemmatized words and
# which souldn't.

mt_analysis_features = {'wn': {'PR_scores': {'file': wn_PR_scores_pickle,
                                             'lem': True,
                                             'log': True},
                               'degrees': {'file': wn_degrees_pickle,
                                           'lem': True,
                                           'log': True},
                               'CCs': {'file': wn_CCs_pickle,
                                       'lem': True,
                                       'log': True},
                               'BCs': {'file': wn_BCs_pickle,
                                       'lem': True,
                                       'log': True},
                               'NSigns': {'file': wn_NSigns_pickle,
                                          'lem': True,
                                          'log': True},
                               'MNSyns': {'file': wn_MNSyns_pickle,
                                          'lem': True,
                                          'log': True}},
                        'fa': {'PR_scores': {'file': fa_norms_PR_scores_pickle,
                                             'lem': True,
                                             'log': True}},
                        'cmu': {'MNsyllables': {'file': cmu_MNsyllables_pickle,
                                                'lem': False,
                                                'log': False},
                                'MNphonemes': {'file': cmu_MNphonemes_pickle,
                                               'lem': False,
                                               'log': False}},
                        'aoa': {'Kuperman': {'file': aoa_Kuperman_pickle,
                                             'lem': True,
                                             'log': False}}}


# Folder to store figures into

mt_analysis_figures_rel = 'figures'
mt_analysis_figures = os.path.join(data_root,
                                   mt_analysis_figures_rel)
mt_analysis_figure_file = os.path.join(mt_analysis_figures, '{}.png')
check_folder(mt_analysis_figures)


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
