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
                                       'the command line.'))
    p.add_argument('--no_multi-thread', dest='multi_thread',
                   action='store_const', const=False, default=True,
                   help=('deactivate multi-threading (default: multi-thread '
                         'to use all processors but one)'))
    p.add_argument('--resume', dest='resume',
                   action='store_const', const=True, default=False,
                   help=('resume a previously interrupted analysis: if the '
                         'script finds some files it was supposed to create, '
                         'it will just skip the corresponding analysis and '
                         'continue with the rest. Otherwise it will abort.'))
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
                         'POS are taken into account).'),
                   choices=st.memetracker_subst_POSs)
    p.add_argument('--ffs', action='store', nargs='+', required=True,
                   help=('space-separated list of datasets on which the '
                         'analysis is done: '
                         "'full': the full clusters; "
                         "'framed': the framed clusters; "
                         "'filtered': the filtered clusters; "
                         "'ff': the framed-filtered clusters."),
                   choices=['full', 'framed', 'filtered', 'ff'])
    p.add_argument('--substitutionss', action='store', nargs='+',
                   required=True,
                   help=('analyze substitutions from the root quote, from '
                         'successive timebags, or based on the appearance '
                         "times of quotes. 'root': from root; 'tbgs': "
                         "from successive timebags; 'cumtbgs': from "
                         "cumulated timebags; 'time': based on "
                         'appearance times. This should be a space-'
                         'separated list of such arguments.'),
                   choices=['root', 'tbgs', 'cumtbgs', 'time'])
    p.add_argument('--substringss', action='store', nargs='+', required=True,
                   help=('1: include substrings as accepted substitutions'
                         "0: don't include substrings (i.e. only strings of "
                         'the same length. This should be a space-separated '
                         'list of such arguments.'),
                   choices=['0', '1'])
    
    # Get the actual arguments.
    
    args = p.parse_args()
    n_timebags_list = [int(ntb) for ntb in args.n_timebagss]
    
    # Run a few checks on the arguments.
    
    if min(n_timebags_list) <= 1:
        raise Exception(('The number of timebags requested must be at least '
                         '2!'))
    
    return args


if __name__ == '__main__':
    
    args = get_args_from_cmdline()
    sa = SubstitutionAnalysis()
    
    if args.multi_thread:
        
        sa.analyze_all_mt(args)
    
    else:
        
        print
        print 'Deactivating multi-threading.'
        sa.analyze_all(args)
