#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from __future__ import division

from warnings import warn

from numpy import array
import pylab as pl

import datainterface.picklesaver as ps
from analyze.memetracker import SubstitutionAnalysis
from results.memetracker import DictNS, clids, cl_means, plot_substseries
import visualize.annotations as an
import settings as st

 
def side_plotter(ax_list, annotedict):
    ax1, ax2 = ax_list
    
    ax1.cla()
    ax1.hist(annotedict['ref'], 50, color='blue', label='Score pool',
            normed=True)
    ax1.legend()
    
    ax2.cla()
    bins = ax2.hist(annotedict['mes_old'], 30, color='cyan',
                    label='Old words', normed=True)[1]
    ax2.hist(annotedict['mes_new'], bins=bins, color='magenta', alpha=0.4,
             label='New words', normed=True)
    ax2.legend()


def plot_all_results(substitutions, substrings):
    """Plot results for given parameters for 'substitutions' and
    'substrings'."""
    parameters_d = []
    
    wn_PR_scores_a = []
    wn_PR_scores_r_avgs = []
    wn_PR_scores_r_stds = []
    wn_PR_scores_r_lens = []
    wn_PR_scores_r_clids = []
    wn_degrees_a = []
    wn_degrees_r_avgs = []
    wn_degrees_r_stds = []
    wn_degrees_r_lens = []
    wn_degrees_r_clids = []
    fa_PR_scores_a = []
    fa_PR_scores_r_avgs = []
    fa_PR_scores_r_stds = []
    fa_PR_scores_r_lens = []
    fa_PR_scores_r_clids = []
    
    sa = SubstitutionAnalysis()
    args = DictNS({'n_timebagss': ['2', '3', '4', '5'],
                   'POSs': st.memetracker_subst_POSs,
                   'ffs': ['filtered', 'ff'],
                   'substringss': [substrings],
                   'substitutionss': [substitutions],
                   'resume': False})
    argsets = sa.create_argsets(args)
    
    for argset in argsets:
        
        # Load the data.
        
        pickle_files = sa.get_save_files(argset, readonly=True)
        
        if pickle_files == None:
            continue
        
        wn_PR_scores = ps.load(pickle_files['wn_PR_scores'])
        wn_PR_scores_d = ps.load(pickle_files['wn_PR_scores_d'])
        wn_degrees = ps.load(pickle_files['wn_degrees'])
        wn_degrees_d = ps.load(pickle_files['wn_degrees_d'])
        fa_PR_scores = ps.load(pickle_files['fa_PR_scores'])
        fa_PR_scores_d = ps.load(pickle_files['fa_PR_scores_d'])
        
        if (len(wn_PR_scores) <= 1 or
            len(wn_degrees) <= 1 or
            len(fa_PR_scores) <= 1):
            warn('{}: empty data'.format(argset))
            continue
        
        # Compute ratios, correct them to represent the means
        # by clusters.
        
        wn_PR_scores_clids = clids(wn_PR_scores_d)
        wn_PR_scores_r = cl_means(wn_PR_scores[:,1] / wn_PR_scores[:,0],
                                  wn_PR_scores_clids)
        wn_degrees_clids = clids(wn_degrees_d)
        wn_degrees_r = cl_means(wn_degrees[:,1] / wn_degrees[:,0],
                                wn_degrees_clids)
        fa_PR_scores_clids = clids(fa_PR_scores_d)
        fa_PR_scores_r = cl_means(fa_PR_scores[:,1] / fa_PR_scores[:,0],
                                  fa_PR_scores_clids)
        
        # Store results.
        
        parameters_d.append(argset)
        
        wn_PR_scores_a.append(wn_PR_scores)
        wn_PR_scores_r_avgs.append(wn_PR_scores_r.mean())
        wn_PR_scores_r_stds.append(wn_PR_scores_r.std())
        wn_PR_scores_r_lens.append(len(wn_PR_scores_r))
        wn_PR_scores_r_clids.append(wn_PR_scores_clids)
        wn_degrees_a.append(wn_degrees)
        wn_degrees_r_avgs.append(wn_degrees_r.mean())
        wn_degrees_r_stds.append(wn_degrees_r.std())
        wn_degrees_r_lens.append(len(wn_degrees_r))
        wn_degrees_r_clids.append(wn_degrees_clids)
        fa_PR_scores_a.append(fa_PR_scores)
        fa_PR_scores_r_avgs.append(fa_PR_scores_r.mean())
        fa_PR_scores_r_stds.append(fa_PR_scores_r.std())
        fa_PR_scores_r_lens.append(len(fa_PR_scores_r))
        fa_PR_scores_r_clids.append(fa_PR_scores_clids)
    
    
    # Convert the results to Numpy arrays and compute confidence intervals.
    
    wn_PR_scores_r_avgs = array(wn_PR_scores_r_avgs)
    wn_PR_scores_r_stds = array(wn_PR_scores_r_stds)
    wn_PR_scores_r_lens = array(wn_PR_scores_r_lens)
    wn_PR_scores_r_ics = (1.96 * wn_PR_scores_r_stds /
                          pl.sqrt(wn_PR_scores_r_lens - 1))
    wn_degrees_r_avgs = array(wn_degrees_r_avgs)
    wn_degrees_r_stds = array(wn_degrees_r_stds)
    wn_degrees_r_lens = array(wn_degrees_r_lens)
    wn_degrees_r_ics = (1.96 * wn_degrees_r_stds /
                        pl.sqrt(wn_degrees_r_lens - 1))
    fa_PR_scores_r_avgs = array(fa_PR_scores_r_avgs)
    fa_PR_scores_r_stds = array(fa_PR_scores_r_stds)
    fa_PR_scores_r_lens = array(fa_PR_scores_r_lens)
    fa_PR_scores_r_ics = (1.96 * fa_PR_scores_r_stds /
                          pl.sqrt(fa_PR_scores_r_lens - 1))
    
    
    # Build annotations.
    
    wn_PR_v = {}
    wn_DEG_v = {}
    
    for pos in st.memetracker_subst_POSs:
        
        wn_PR = ps.load(st.wordnet_PR_scores_pickle.format(pos))
        wn_DEG = ps.load(st.wordnet_degrees_pickle.format(pos))
        wn_PR_v[pos] = array(wn_PR.values())
        wn_DEG_v[pos] = array(wn_DEG.values())
    
    fa_PR = ps.load(st.freeassociation_norms_PR_scores_pickle)
    fa_PR_v = array(fa_PR.values())
    
    annotes = ['wn_PR: {}\nwn_deg: {}\nfa_PR: {}'.format(n_wn_PR, n_wn_deg,
                                                         n_fa_PR)
               for (n_wn_PR, n_wn_deg, n_fa_PR) in zip(wn_PR_scores_r_lens,
                                                       wn_degrees_r_lens,
                                                       fa_PR_scores_r_lens)]
    wn_PR_annotes = dict(zip(annotes,
                             [{'ref': wn_PR_v[parameters_d[i]['POS']],
                               'mes_old': wn_PR_scores_a[i][:, 0],
                               'mes_new': wn_PR_scores_a[i][:, 1]}
                               for i in range(len(wn_PR_scores_a))]))
    wn_DEG_annotes = dict(zip(annotes,
                              [{'ref': wn_DEG_v[parameters_d[i]['POS']],
                                'mes_old': wn_degrees_a[i][:, 0],
                                'mes_new': wn_degrees_a[i][:, 1]}
                               for i in range(len(wn_degrees_a))]))
    fa_PR_annotes = dict(zip(annotes,
                             [{'ref': fa_PR_v,
                               'mes_old': fa_PR_scores_a[i][:, 0],
                               'mes_new': fa_PR_scores_a[i][:, 1]}
                               for i in range(len(fa_PR_scores_a))]))
   
    # Build data for plotting.
    
    POS_series = []
    cur_POS = None
    ff_series = []
    cur_ff = None
    ntb_series = []
    cur_ntb = None
    
    for x, p in enumerate(parameters_d):
        
        if cur_POS == p['POS']:
            POS_series[-1][1].append(x)
        else:
            POS_series.append([p['POS'], [x]])
            cur_POS = p['POS']
        
        if cur_ff == p['ff']:
            ff_series[-1][1].append(x)
        else:
            ff_series.append([p['ff'], [x]])
            cur_ff = p['ff']
        
        if cur_ntb == p['n_timebags']:
            ntb_series[-1][1].append(x)
        else:
            ntb_series.append([p['n_timebags'], [x]])
            cur_ntb = p['n_timebags']
    
    
    wn_PR_h0 = {}
    wn_DEG_h0 = {}
    fa_PR_h0 = {}
    
    fa_PR = ps.load(st.freeassociation_norms_PR_scores_pickle)
    fa_PR_v = array(fa_PR.values())
    fa_PR_h0_tmp = fa_PR_v.mean() * (1 / fa_PR_v).mean()
    
    for pos in st.memetracker_subst_POSs:
        
        wn_PR = ps.load(st.wordnet_PR_scores_pickle.format(pos))
        wn_PR_v = array(wn_PR.values())
        wn_PR_h0[pos] = wn_PR_v.mean() * (1 / wn_PR_v).mean()
        
        wn_DEG = ps.load(st.wordnet_degrees_pickle.format(pos))
        wn_DEG_v = array(wn_DEG.values())
        wn_DEG_h0[pos] = wn_DEG_v.mean() * (1 / wn_DEG_v).mean()
        
        fa_PR_h0[pos] = fa_PR_h0_tmp
    
    
    # Plot everything
    
    title_wn_sra = \
        'WN PR scores ratio [substitutions={}, substrings={}]'.format(
                                                                substitutions,
                                                                substrings)
    af_wn_sra, af2_wn_sra = plot_substseries(wn_PR_h0, wn_PR_scores_r_avgs,
                                             wn_PR_scores_r_ics,
                                             wn_PR_scores_r_clids,
                                             wn_PR_annotes,
                                             title_wn_sra,
                                             POS_series, ff_series,
                                             parameters_d)
    title_wn_dra = \
        'WN Degrees ratio [substitutions={}, substrings={}]'.format(
                                                                substitutions,
                                                                substrings)
    af_wn_dra, af2_wn_dra = plot_substseries(wn_DEG_h0, wn_degrees_r_avgs,
                                             wn_degrees_r_ics,
                                             wn_degrees_r_clids,
                                             wn_DEG_annotes,
                                             title_wn_dra,
                                             POS_series, ff_series,
                                             parameters_d)
    title_fa_sra = \
        'FA PR scores ratio [substitutions={}, substrings={}]'.format(
                                                                substitutions,
                                                                substrings)
    af_fa_sra, af2_fa_sra = plot_substseries(fa_PR_h0, fa_PR_scores_r_avgs,
                                             fa_PR_scores_r_ics,
                                             fa_PR_scores_r_clids,
                                             fa_PR_annotes,
                                             title_fa_sra,
                                             POS_series, ff_series,
                                             parameters_d)
    
    an.linkAnnotationFinders([af_wn_sra, af_fa_sra, af_wn_dra])
#    af_wn_sra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
#    af_wn_dra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
#    af_fa_sra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])


if __name__ == '__main__':
    
    for substitutions in ['root', 'tbgs', 'time']:
        
        for substrings in ['0', '1']:
            print ('Creating plots for substitutions={}, '
                   'substrings={} ...').format(substitutions, substrings),
            plot_all_results(substitutions, substrings)
            print 'OK'
    
    pl.show()
