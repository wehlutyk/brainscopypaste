#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze the 1-word changes in the MemeTracker dataset.

See analyze.memetracker.SubstitutionAnalysis for full documentation.

Methods:
  * get_args_from_cmdline: get arguments from the command line

"""


import argparse as ap

from datastructure.memetracker_base import list_attributes_trunc
from datastructure.memetracker import Cluster
from analyze.memetracker import SubstitutionAnalysis
import settings as st


def get_args_from_cmdline():
    """Get arguments from the command line.

    The arguments are defined by the 'add_argument' statements. Run this
    script with the '-h' option for help on the arguments.

    """

    # Create the arguments parser.

    p = ap.ArgumentParser(description=('analyze the 1-word changes '
                                       '(hamming_word-distance == 1) '
                                       'in the MemeTracker dataset.'))

    p.add_argument('--ff', action='store', nargs=1, required=True,
                   help=('Specify on what dataset the analysis is done: '
                         "'full': the full clusters; "
                         "'framed': the framed clusters; "
                         "'filtered': the filtered clusters; "
                         "'ff': the framed-filtered clusters."),
                   choices=['full', 'framed', 'filtered', 'ff'])
    p.add_argument('--lemmatizing', action='store', nargs=1, required=True,
                   help=('1: lemmatize words before searching for them '
                         'in the features lists; '
                         "0: don't lemmatize them."),
                   choices=['0', '1'])
    p.add_argument('--substitutions', action='store', nargs=1, required=True,
                   help=('analyze substitutions from the root quote, from '
                         'successive timebags, or based on the appearance '
                         "times of quotes. 'root': from root; 'tbgs': "
                         "from successive timebags; 'cumtbgs': from "
                         "cumulated timebags; 'time': based on "
                         'appearance times.'),
                   choices=list_attributes_trunc(Cluster, 'iter_substitutions_'))
    p.add_argument('--substrings', action='store', nargs=1, required=True,
                   help=('1: include substrings as accepted substitutions'
                         "0: don't include substrings (i.e. only strings of "
                         'the same length.'),
                   choices=['0', '1'])
    p.add_argument('--POS', action='store', nargs=1, required=True,
                   help=('select what POS to analyze. Valid values are '
                         "'a', 'n', 'v', 'r', or 'all' (in which case only "
                         'substitutions where words have the same POS are '
                         'taken into account).'),
                   choices=st.memetracker_subst_POSs)
    p.add_argument('--verbose', dest='verbose', action='store_const',
                   const=True, default=False,
                   help=('print out the transitions compared, their '
                         'processing, and if they are stored of not'))
    p.add_argument('--n_timebags', action='store', nargs=1, required=True,
                   help='number of timebags to cut the clusters into')

    # Get the actual arguments.

    args = p.parse_args()

    ff = args.ff[0]
    lemmatizing = bool(int(args.lemmatizing[0]))
    substitutions = args.substitutions[0]
    substrings = bool(int(args.substrings[0]))
    POS = args.POS[0]
    n_timebags = int(args.n_timebags[0])

    return {'ff': ff,
            'lemmatizing': lemmatizing,
            'substitutions': substitutions,
            'substrings': substrings,
            'POS': POS,
            'verbose': args.verbose,
            'n_timebags': n_timebags,
            'resume': False}


if __name__ == '__main__':
    args = get_args_from_cmdline()
    sa = SubstitutionAnalysis()
    sa.analyze(args)
