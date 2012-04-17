#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes in the MemeTracker dataset.

This script looks at features of words that are substituted through time in
the MemeTracker Clusters. The features are the Wordnet PageRank scores of the
words, and their degree in the Wordnet graph.

Details:
  The script takes each Cluster (framed or not, depending on the '--framing'
  option), splits it into a number of TimeBags, then looks at the transitions
  between TimeBags defined by the 'bag_transitions' variable: for each
  transition (e.g. TimeBag #0 to TimeBag #2), it takes the highest frequency
  string in the first TimeBag, gets all strings in the second TimeBag which
  are at hamming_word-distance == 1, and looks at any substitutions: when a
  substitution is found, depending on the parameters it can go through the
  following:
    * get excluded if both words (substituted and substitutant) aren't from
      the same grammatical category ('--same_POS' option)
    * the substituted and substitutant word can be lemmatized ('--lemmatize'
      option)
  Once that processing is done, the features of the substituted word and the
  new word are stored. If any one of those words is not referenced in the
  features (e.g. is not the PR scores list), it takes note of it (in the
  'nonlemmas' variable). It then saves all the data to pickle files.

The output is as follows (see settings.py for the full filenames):
  * one file containing the PR scores of (substituted word, new word) couples
    (which is a Nx2 numpy array)
  * one file containing the degrees of (substituted word, new word) couples
    (again a Nx2 numpy array)
  * one file containing a list of dicts with data about the words that didn't
    have associated features (the data stored is: cluster id ('cl_id'),
    tokenized start string ('smax_tok'), tokenized end string ('s_tok')
    and index of the changed word ('idx')).

"""


from __future__ import division

import argparse as ap

from nltk.corpus import wordnet as wn
import numpy as np

from linguistics.memetracker import levenshtein
from linguistics.treetagger import TreeTaggerTags
import datainterface.picklesaver as ps
import settings as st


def get_arguments():
    """Get arguments from the command line."""
    
    # Create the arguments parser.
    
    p = ap.ArgumentParser(description=('analyze the 1-word changes '
                                       '(hamming_word-distance == 1) '
                                       'in the MemeTracker dataset.'))
    
    p.add_argument('--framing', action='store',
                   nargs=1, required=True,
                   help=('1: analyze framed clusters; '
                         '0: analyse non-framed clusters.'))
    p.add_argument('--lemmatizing', action='store',
                   nargs=1, required=True,
                   help=('1: lemmatize words before searching for them '
                         'in the features lists; '
                         "0: don't lemmatize them."))
    p.add_argument('--same_POS', action='store',
                   nargs=1, required=True,
                   help=('1: only save substitutions where both words are '
                         "tagged as the same POS tag; 0: don't apply that "
                         'filter'))
    p.add_argument('--verbose', dest='verbose', action='store_const',
                   const=1, default=0,
                   help=('print out the transitions compared, their '
                         'processing, and if they are stored of not'))
    p.add_argument('--n_timebags', action='store',
                   nargs=1, required=True,
                   help='number of timebags to cut the clusters into')
    p.add_argument('transitions', action='store',
                   nargs='+',
                   help=('space-separated list of transitions between '
                         'timebags that are to be examined, in format '
                         "'n1-n2' where n1 and n2 are the indices of "
                         "the timebags (starting at 0); e.g. '0-1 1-2'."))
    
    # Get the actual arguments.
    
    args = p.parse_args()
    
    framing = int(args.framing[0])
    lemmatizing = int(args.lemmatizing[0])
    same_POS = int(args.same_POS[0])
    n_timebags = int(args.n_timebags[0])
    bag_transitions = [(int(s.split('-')[0]), int(s.split('-')[1]))
                       for s in args.transitions]
    
    # Run a few checks on the arguments.
    
    all_idx = [i for tr in bag_transitions for i in tr]
    
    if max(all_idx) >= n_timebags or min(all_idx) < 0:
        raise Exception(('Wrong bag transitions, according to the '
                         'number of timebags requested'))
    
    if framing != 0 and framing != 1:
        raise Exception('Wrong value for --framing. Expected 1 or 0.')
    
    if lemmatizing != 0 and lemmatizing != 1:
        raise Exception('Wrong value for --lemmatizing. Expected 1 or 0.')
    
    if same_POS != 0 and same_POS != 1:
        raise Exception('Wrong value for --same_POS. Expected 1 or 0.')
    
    return {'framing': bool(framing),
            'lemmatizing': bool(lemmatizing),
            'same_POS': bool(same_POS),
            'verbose': bool(args.verbose),
            'n_timebags': n_timebags,
            'bag_transitions': bag_transitions}


def get_save_files(args):
    """Get the filenames where data is to be saved; check they don't exist."""
    
    # Create the file prefix according to 'args'.

    file_prefix = ''
    
    if not args['framing']:
        file_prefix += 'N'
    
    file_prefix += 'F_'
    
    if not args['lemmatizing']:
        file_prefix += 'N'
    
    file_prefix += 'L_'
    
    if not args['same_POS']:
        file_prefix += 'N'
    
    file_prefix += 'P_'
    file_prefix += str(args['n_timebags']) + '_'
    
    for (i, j) in args['bag_transitions']:
        file_prefix += '{}-{}_'.format(i, j)
    
    pickle_transitionPRscores = \
        st.memetracker_subst_transitionPRscores_pickle.format(file_prefix)
    pickle_transitiondegrees = \
        st.memetracker_subst_transitiondegrees_pickle.format(file_prefix)
    
    # Check that the destinations don't already exist.
    
    st.check_file(pickle_transitionPRscores)
    st.check_file(pickle_transitiondegrees)
    
    return {'transitionPRscores': pickle_transitionPRscores,
            'transitiondegrees': pickle_transitiondegrees}


def load_data(args):
    """Load the data from pickle files."""
    print
    print 'Doing analysis with the following parameters:'
    print '  framing = {}'.format(args['framing'])
    print '  lemmatizing = {}'.format(args['lemmatizing'])
    print '  same_POS = {}'.format(args['same_POS'])
    print '  verbose = {}'.format(args['verbose'])
    print '  n_timebags = {}'.format(args['n_timebags'])
    print '  transitions = {}'.format(args['bag_transitions'])
    print
    print 'Loading cluster, PageRank, and degree data...',
    
    if args['framing']:
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
    
    tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                            TAGINENC='utf-8', TAGOUTENC='utf-8')
    
    # Results of the analysis
    
    transitionPRscores = []
    transitiondegrees = []
    n_stored = 0
    n_all = 0
    
    # Progress info
    
    progress = 0
    n_clusters = len(data['clusters'])
    info_step = max(int(round(n_clusters / 100)), 1)
    
    for cl in data['clusters'].itervalues():
        
        # Progress info
        
        progress += 1
        
        if progress % info_step == 0:
            
            print '  {} % ({} / {} clusters)'.format(
                int(round(100 * progress / n_clusters)), progress, n_clusters)
        
        
        # Get timebags and examine transitions.
        
        tbgs = cl.build_timebags(args['n_timebags'])
        
        for i, j in args['bag_transitions']:
            
            # Highest freq string and its daughters
            # (sphere of hamming_word distance =1)
            
            smax = tbgs[i].max_freq_string.lower()
            smax_pos = tagger.Tags(smax)
            smax_tok = tagger.Tokenize(smax)
            daughters = [tbgs[j].strings[k].lower()
                         for k in tbgs[j].hamming_word_sphere(smax, 1)]
            
            for s in daughters:
                
                n_all += 1
                
                # Find the word that was changed.
                
                s_pos = tagger.Tags(s)
                s_tok = tagger.Tokenize(s)
                idx = np.where([w1 != w2 for (w1, w2) in
                                zip(s_tok, smax_tok)])[0]
                
                
                # Verbose info
                
                if args['verbose']:
                    
                    print
                    print ("***** SUBST (cl #{}) ***** '".format(cl.id) +
                           '{}/{}'.format(smax_tok[idx], smax_pos[idx]) +
                           "' -> '" + '{}/{}'.format(s_tok[idx], s_pos[idx]) +
                           "'")
                    print smax
                    print '=>'
                    print s
                    print
                
                
                # Check the POS tags if asked to.
                
                if args['same_POS']:
                    
                    if s_pos[idx][:2] != smax_pos[idx][:2]:
                        
                        if args['verbose']:
                            
                            print 'Not stored (not same POS)'
                            raw_input()
                        
                        break
                
                
                # Lemmatize the words if asked to.
                
                if args['lemmatizing']:
                    
                    m1 = wn.morphy(smax_tok[idx])
                    if m1 != None:
                        lem1 = m1
                    else:
                        lem1 = smax_tok[idx]
                    
                    m2 = wn.morphy(s_tok[idx])
                    if m2 != None:
                        lem2 = m2
                    else:
                        lem2 = s_tok[idx]
                    
                    # Verbose info
                    
                    if args['verbose']:
                        print "Lemmatized to '" + lem1 + "' -> '" + lem2 + "'"
                    
                else:
                    
                    lem1 = smax_tok[idx]
                    lem2 = s_tok[idx]
                
                
                # Exclude if this isn't really a substitution.
                
                if levenshtein(lem1, lem2) <= 1:
                    
                    # Verbose info
                    
                    if args['verbose']:
                        
                        print 'Not stored (not subst)'
                        raw_input()
                    
                    break
                
                
                # Look the words up in the features lists.
                
                try:
                    
                    transitionPRscores.append([data['PR'][lem1],
                                               data['PR'][lem2]])
                    transitiondegrees.append([data['degrees'][lem1],
                                              data['degrees'][lem2]])
                    n_stored += 1
                    
                    # Verbose info
                    
                    if args['verbose']:
                        print 'Stored'
                    
                except KeyError:
                    
                    # Verbose info
                    
                    if args['verbose']:
                        print 'Not stored (not ref)'
                
                
                # Pause to read verbose info.
                
                if args['verbose']:
                    raw_input()
    
    
    print
    print 'Stored {} of {} substitutions examined.'.format(n_stored, n_all)
    
    return {'transitionPRscores': transitionPRscores,
            'transitiondegrees': transitiondegrees}


def save_data(files, results):
    """Save the analysis data to pickle files."""
    print
    print 'Done. Saving data...',
    
    ps.save(np.array(results['transitionPRscores']),
            files['transitionPRscores'])
    ps.save(np.array(results['transitiondegrees']),
            files['transitiondegrees'])

    print 'OK'


if __name__ == '__main__':
    args = get_arguments()
    files = get_save_files(args)
    data = load_data(args)
    results = analyze(args, data)
    save_data(files, results)
