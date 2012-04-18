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


import argparse as ap

from analyze.memetracker import SubstitutionAnalysis


def get_args_from_cmdline():
    """Get arguments from the command line."""
    
    # Create the arguments parser.
    
    p = ap.ArgumentParser(description=('analyze the 1-word changes '
                                       '(hamming_word-distance == 1) '
                                       'in the MemeTracker dataset.'))
    
    p.add_argument('--framing', action='store', nargs=1, required=True,
                   help=('1: analyze framed clusters; '
                         '0: analyse non-framed clusters.'))
    p.add_argument('--lemmatizing', action='store', nargs=1, required=True,
                   help=('1: lemmatize words before searching for them '
                         'in the features lists; '
                         "0: don't lemmatize them."))
    p.add_argument('--same_POS', action='store', nargs=1, required=True,
                   help=('1: only save substitutions where both words '
                         "are tagged as the same POS tag; 0: don't apply "
                         'that filter'))
    p.add_argument('--verbose', dest='verbose', action='store_const',
                   const=1, default=0,
                   help=('print out the transitions compared, their '
                         'processing, and if they are stored of not'))
    p.add_argument('--n_timebags', action='store', nargs=1, required=True,
                   help='number of timebags to cut the clusters into')
    p.add_argument('transitions', action='store', nargs='+',
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


if __name__ == '__main__':
    args = get_args_from_cmdline()
    sa = SubstitutionAnalysis()
    data = sa.load_data(args['framing'])
    sa.analyze(args, data)
