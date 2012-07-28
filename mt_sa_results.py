#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from __future__ import division

import argparse as ap

from numpy import array
import pylab as pl

from analyze.memetracker import gen_results_dict
import results.memetracker as r_mt
import settings as st


def get_args_from_cmdline():

    p = ap.ArgumentParser(description=('Needs doc.'))
    p.add_argument('--substitutionss', action='store', nargs='+',
                   required=True,
                   help=('Needs doc.'),
                   choices=['root', 'tbgs', 'cumtbgs', 'time'])
    p.add_argument('--substringss', action='store', nargs='+', required=True,
                   help=('Needs doc.'),
                   choices=['0', '1'])
    return p.parse_args()


def plot_results(substitutions, substrings):
    """Plot results for given parameters for 'substitutions' and
    'substrings'."""

    # Prepare some parameters

    args = r_mt.DictNS({'n_timebagss': ['2', '3', '4', '5'],
                        'POSs': st.memetracker_subst_POSs,
                        'ffs': ['filtered', 'ff'],
                        'substringss': [substrings],
                        'substitutionss': [substitutions],
                        'resume': False})

    # Get the results corresponding to args.

    argsets, results, suscept_data = r_mt.load_ratio_results(args)

    # Reformat the data and build annotations and H0s.

    annotes = {}
    H0s = gen_results_dict(dict)
    features = r_mt.load_features()
    fvalues = r_mt.features_to_values(features)

    for fdata, ffiles in st.memetracker_subst_features.iteritems():

        annotes[fdata] = {}
        for fname in ffiles.iterkeys():

            # Convert the results to Numpy arrays and compute confidence intervals

            results[fdata][fname]['r_avgs'] = array(results[fdata][fname]['r_avgs'])
            results[fdata][fname]['r_stds'] = array(results[fdata][fname]['r_stds'])
            results[fdata][fname]['r_lens'] = array(results[fdata][fname]['r_lens'])
            results[fdata][fname]['r_ics'] = (1.96 * results[fdata][fname]['r_stds'] /
                                              pl.sqrt(results[fdata][fname]['r_lens'] - 1))
            results[fdata][fname]['r_h0s'] = array(results[fdata][fname]['r_h0s'])

            # Build annotations.

            annotes[fdata][fname] = [{'text': fname + ': {}'.format(l),
                                      'argset': argset, 'fdata': fdata,
                                      'fname': fname}
                                     for l, argset
                                     in zip(results[fdata][fname]['r_lens'], argsets)]

            # Build the H0 values for comparison w/ respect to feature sets

            for pos in st.memetracker_subst_POSs:
                H0s[fdata][fname][pos] = (fvalues[fdata][fname][pos].mean()
                                          * (1 / fvalues[fdata][fname][pos]).mean())

    # Build categories for plotting the colors of the columns.

    POS_series = []
    cur_POS = None

    ntb_series = []
    cur_ntb = None

    for x, p in enumerate(argsets):

        if cur_POS == p['POS']:
            POS_series[-1][1].append(x)
        else:
            POS_series.append([p['POS'], [x]])
            cur_POS = p['POS']

        if cur_ntb == p['n_timebags']:
            ntb_series[-1][1].append(x)
        else:
            ntb_series.append([p['n_timebags'], [x]])
            cur_ntb = p['n_timebags']

    # Plot everything

    for fdata, ffiles in st.memetracker_subst_features.iteritems():

        for fname in ffiles.iterkeys():

            title = (fdata + ' ' + fname
                     + ' ratio [substitutions={}, '.format(substitutions)
                     + 'substrings={}]'.format(substrings))

            r_mt.plot_substseries(H0s[fdata][fname],
                                  results[fdata][fname]['r_h0s'],
                                  fvalues[fdata][fname],
                                  features[fdata][fname],
                                  results[fdata][fname]['r_avgs'],
                                  results[fdata][fname]['r_ics'],
                                  results[fdata][fname]['r_clids'],
                                  annotes[fdata][fname], title,
                                  POS_series, argsets)


if __name__ == '__main__':

    args = get_args_from_cmdline()

    for substitutions in args.substitutionss:

        for substrings in args.substringss:

            print ('Creating plots for substitutions={}, '
                   'substrings={} ...').format(substitutions, substrings),
            plot_results(substitutions, substrings)
            print 'OK'

    pl.show()
