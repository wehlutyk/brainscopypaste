#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes in the MemeTracker dataset.

This script looks at features of words that are substituted through time in
the MemeTracker Clusters. The features are the Wordnet PageRank scores of the
words, and their degree in the Wordnet graph.

Details:
  The script takes each Cluster, splits it into a number of TimeBags, then
  looks at the transitions between TimeBags defined by the 'bag_transitions'
  variable: for each transition (e.g. TimeBag #0 to TimeBag #2), it takes the
  highest frequency string in the first TimeBag, gets all strings in the
  second TimeBag which are at hamming_word-distance == 1, and stores the
  features of the substituted word and the new word. If any one of those
  words is not referenced in the features (e.g. is not the PR scores list),
  it takes note of it (in the 'nonlemmas' variable). It then saves all the
  data to pickle files.

The output is as follows (see settings.py for the full filenames):
  * one file containing the PR scores of (substituted word, new word) couples
    (which is a Nx2 numpy array)
  * one file containing the degrees of (substituted word, new word) couples
    (again a Nx2 numpy array)
  * one file containing a list of dicts with data about the words that didn't
    have associated features (the data stored is: cluster id ('cl_id'),
    tokenized start string ('t_smax'), tokenized end string ('t_s')
    and index of the changed word ('idx')).

"""


from __future__ import division

import argparse as ap
from textwrap import dedent

from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
import numpy as np

import datainterface.picklesaver as ps
import settings as st


def get_arguments():
    """Get arguments from the command line."""
    
    # Create the arguments parser.
    
    p = ap.ArgumentParser(description=dedent('''\
                                             Analyze the 1-word changes \
                                             (hamming_word-distance == 1) \
                                             in the MemeTracker dataset.\
                                             '''))
    
    p.add_argument('--framing', action='store',
                   nargs=1, required=True,
                   help=dedent('''\
                               1: analyze framed clusters; \
                               0: analyse non-framed clusters.\
                               '''))
    p.add_argument('--lemmatizing', action='store',
                   nargs=1, required=True,
                   help=dedent("""\
                               1: lemmatize words before searching for them  \
                               in the features lists; \
                               0: don't lemmatize them.\
                               """))
    p.add_argument('--n_timebags', action='store',
                   nargs=1, required=True,
                   help='Number of timebags to cut the clusters into')
    p.add_argument('transitions', action='store',
                   nargs='+',
                   help=dedent("""\
                               Space-separated list of transitions between \
                               timebags that are to be examined, in format \
                               'n1-n2' where n1 and n2 are the indices of \
                               the timebags (starting at 0); \
                               e.g. '0-1 1-2'.\
                               """))
    
    # Get the actual arguments.
    
    args = p.parse_args()
    
    framing = int(args.framing[0])
    lemmatizing = int(args.lemmatizing[0])
    n_timebags = int(args.ntimebags[0])
    bag_transitions = [(int(s.split('-')[0]), int(s.split('-')[1]))
                       for s in args.transitions]
    
    # Run a few checks on the arguments.
    
    all_idx = [i for tr in bag_transitions for i in tr]
    
    if max(all_idx) >= n_timebags or min(all_idx) < 0:
        raise Exception(dedent('''\
                               Wrong bag transitions, according to the \
                               number of timebags requested\
                               '''))
    
    if framing != 0 and framing != 1:
        raise Exception('Wrong value for --framing. Expected 1 or 0.')
    
    if lemmatizing != 0 and lemmatizing != 1:
        raise Exception('Wrong value for --lemmatizing. Expected 1 or 0.')
    
    return {'framing': framing,
            'lemmatizing': lemmatizing,
            'n_timebags': n_timebags,
            'bag_transitions': bag_transitions}


def get_save_files(args):
    """Get the filenames where data is to be saved; check they don't exist."""
    
    # Create the file prefix according to 'args'.

    file_prefix = ''
    
    if args.framing == 0:
        file_prefix += 'N'
    
    file_prefix += 'F_'
    
    if args.lemmatizing == 0:
        file_prefix += 'N'
    
    file_prefix += 'L_'
    
    file_prefix += 'S_'
    file_prefix += str(args.n_timebags) + '_'
    
    for (i, j) in args.bag_transitions:
        file_prefix += '{}-{}_'.format(i, j)
    
    pickle_transitionPRscores = \
        st.memetracker_subst_transitionPRscores_pickle.format(file_prefix)
    pickle_transitiondegrees = \
        st.memetracker_subst_transitiondegrees_pickle.format(file_prefix)
    pickle_nonlemmas = \
        st.memetracker_subst_nonlemmas_pickle.format(file_prefix)
    
    # Check that the destinations don't already exist.
    
    st.check_file(pickle_transitionPRscores)
    st.check_file(pickle_transitiondegrees)
    st.check_file(pickle_nonlemmas)
    
    return {'PRscores': pickle_transitionPRscores,
            'degrees': pickle_transitiondegrees,
            'nonlemmas': pickle_nonlemmas}


def load_data(args):
    """Load the data from pickle files."""
    print
    print 'Doing analysis with the following parameters:'
    print '  framing = {}'.format(args.framing)
    print '  lemmatizing = {}'.format(args.lemmatizing)
    print '  n_timebags = {}'.format(args.n_timebags)
    print '  transitions = {}'.format(args.bag_transitions)
    print
    print 'Loading cluster, PageRank, and degree data...',
    
    if args.framing == 1:
        clusters = ps.load(st.memetracker_full_framed_pickle)
    else:
        clusters = ps.load(st.memetracker_full_pickle)
    
    PR = ps.load(st.wordnet_PR_scores_pickle)
    degrees = ps.load(st.wordnet_degrees_pickle)
    
    print 'OK'
    
    return {'clusters': clusters, 'PR': PR, 'degrees': degrees}


def analyze(args, data):
    """Do the substitution analysis."""
    print
    print 'Doing substitution analysis:'
    
    lemmatizer = WordNetLemmatizer()
    
    # Results of the analysis
    
    transitionPRscores = []
    transitiondegrees = []
    nonlemmas = []
    
    # Progress info
    
    progress = 0
    n_clusters = len(data.clusters)
    info_step = max(int(round(n_clusters / 100)), 1)
    
    for cl in data.clusters.itervalues():
        
        # Progress info
        
        progress += 1
        
        if progress % info_step == 0:
            print '  {} % ({} / {} clusters)'.format(
                int(round(100 * progress / n_clusters)), progress, n_clusters)
        
        # Get timebags and examine transitions.
        
        tbgs = cl.build_timebags(args.n_timebags)
        
        for i, j in args.bag_transitions:
            
            # Highest freq string and its daughters
            # (sphere of hamming_word distance =1)
            
            smax = tbgs[i].max_freq_string
            daughters = [tbgs[j].strings[k]
                         for k in tbgs[j].hamming_word_sphere(smax, 1)]
            
            for s in daughters:
                
                # Find the word that was changed.
                
                t_smax = word_tokenize(smax)
                t_s = word_tokenize(s)
                idx = np.where([w1 != w2 for (w1, w2) in zip(t_s, t_smax)])[0]
                
                # Lemmatize the words if asked to.
                
                if args.lemmatizing == 1:
                    
                    lem1 = lemmatizer.lemmatize(t_smax[idx]).lower()
                    lem2 = lemmatizer.lemmatize(t_s[idx]).lower()
                    
                else:
                    
                    lem1 = t_smax[idx].lower()
                    lem2 = t_s[idx].lower()
                
                # Store the features in both words are in the features lists.
                
                try:
                    
                    transitionPRscores.append([data.PR[lem1], data.PR[lem2]])
                    transitiondegrees.append([data.degrees[lem1],
                                              data.degrees[lem2]])
                    
                except KeyError:
                    
                    # If not, keep track of what we left out
                    
                    nonlemmas.append({'cl_id': cl.id, 't_s': t_s, 
                                      't_smax': t_smax, 'idx': idx})
    
    return {'transitionPRscores': transitionPRscores,
            'transitiondegrees': transitiondegrees,
            'nonlemmas': nonlemmas}


def save_data(files, results):
    """Save the analysis data to pickle files."""
    print
    print 'Done. Saving data...',
    
    ps.save(np.array(results.transitionPRscores),
            files.pickle_transitionPRscores)
    ps.save(np.array(results.transitiondegrees),
            files.pickle_transitiondegrees)
    ps.save(results.nonlemmas, files.pickle_nonlemmas)

    print 'OK'


if __name__ == '__main__':
    args = get_arguments()
    files = get_save_files(args)
    data = load_data(args)
    results = analyze(args, data)
    save_data(files, data)
