#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Do the MemeTracker substitution analysis with a number of timebag slicings.

Methods:
  * get_args_from_cmdline: get the timebag slicings from the
                                      command line

"""


import argparse as ap

from analyze.memetracker import SubstitutionAnalysis


def get_args_from_cmdline():
    """Get the timebag slicings from the command line.
    
    The syntax is defined by the 'add_argument' statement. Run this script
    with the '-h' option for help on the exact syntax.
    
    """
    
    # Create the arguments parser.
    
    p = ap.ArgumentParser(description=('run the substitution analysis '
                                       'with a number timebag slicings, '
                                       'specified at the command line. This '
                                       'is done on the framed clusters, with '
                                       'lemmatizing and the same_POS option '
                                       'activated.'))
    p.add_argument('--no_multi-thread', dest='multi_thread',
                   action='store_const', const=False, default=True,
                   help=('deactivate multi-threading (default: multi-thread '
                         'to use all processors but one)'))
    p.add_argument('n_timebags_list', action='store', nargs='+',
                   help=('space-separated list of timebag slicings to '
                         "examine. e.g. '2 3 4' will run the substitution "
                         'analysis cutting clusters in 2, then 3, then 4 '
                         'timebags, and examining all possible transitions '
                         'each time.'))
    
    # Get the actual arguments.
    
    args = p.parse_args()
    n_timebags_list = [int(ntb) for ntb in args.n_timebags_list]
    
    # Run a few checks on the arguments.
    
    if min(n_timebags_list) <= 1:
        raise Exception(('The number of timebags requested must be at least '
                         '2!'))
    
    return (args.multi_thread, n_timebags_list)


if __name__ == '__main__':
    
    (multi_thread, n_timebags_list) = get_args_from_cmdline()
    sa = SubstitutionAnalysis()
    
    if multi_thread:
        
        sa.analyze_all_mt(n_timebags_list)
    
    else:
        
        print
        print 'Deactivating multi-threading.'
        sa.analyze_all(n_timebags_list)
