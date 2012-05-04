#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Do the MemeTracker substitution analysis with a number of timebag slicings.

Methods:
  * get_args_from_cmdline: get the timebag slicings from the command line

"""


import argparse as ap

from analyze.memetracker import SubstitutionAnalysis
import settings as st


def get_args_from_cmdline():
    """Get the timebag slicings from the command line.
    
    The syntax is defined by the 'add_argument' statement. Run this script
    with the '-h' option for help on the exact syntax.
    
    """
    
    # Create the arguments parser.
    
    p = ap.ArgumentParser(description=('run the substitution analysis '
                                       'with a number timebag slicings and '
                                       'POS tags to compare, specified at '
                                       'the command line. This is done on '
                                       'the framed-filtered  clusters, with '
                                       'lemmatizing activated.'))
    p.add_argument('--no_multi-thread', dest='multi_thread',
                   action='store_const', const=False, default=True,
                   help=('deactivate multi-threading (default: multi-thread '
                         'to use all processors but one)'))
    p.add_argument('--n_timebagss', action='store', nargs='+', required=True,
                   help=('space-separated list of timebag slicings to '
                         "examine. e.g. '2 3 4' will run the substitution "
                         'analysis cutting clusters in 2, then 3, then 4 '
                         'timebags, and examining all possible transitions '
                         'each time.'))
    p.add_argument('--POSs', action='store', nargs='+', required=True,
                   help=('space-seperated list of POS tags to examine. Valid'
                         "values are 'a', 'n', 'v', 'r', or 'all' (in which"
                         'case only substitutions where words have the same '
                         'POS are taken into account).'))
    
    # Get the actual arguments.
    
    args = p.parse_args()
    n_timebags_list = [int(ntb) for ntb in args.n_timebagss]
    
    # Run a few checks on the arguments.
    
    if min(n_timebags_list) <= 1:
        raise Exception(('The number of timebags requested must be at least '
                         '2!'))
    
    for pos in args.POSs:
        
        if pos not in st.memetracker_subst_POSs:
            raise Exception(('Wrong value for POS: expected a '
                             'list of elements from '
                             '{}.').format(st.memetracker_subst_POSs))
    
    return (args.multi_thread, n_timebags_list, args.POSs)


if __name__ == '__main__':
    
    (multi_thread, n_timebags_list, POSs) = get_args_from_cmdline()
    sa = SubstitutionAnalysis()
    
    if multi_thread:
        
        sa.analyze_all_mt(n_timebags_list, POSs)
    
    else:
        
        print
        print 'Deactivating multi-threading.'
        sa.analyze_all(n_timebags_list, POSs)
