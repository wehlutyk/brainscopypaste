#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes in the MemeTracker dataset.

See analyze.memetracker.SubstitutionAnalysis for full documentation.

Methods:
  * get_args_from_cmdline: get arguments from the command line

"""


import argparse as ap

from analyze.memetracker import SubstitutionAnalysis


def get_args_from_cmdline():
    """Get arguments from the command line.
    
    The arguments are defined by the 'add_argument' statements. Run this
    script with the '-h' option for help on the arguments.
    
    """
    
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
