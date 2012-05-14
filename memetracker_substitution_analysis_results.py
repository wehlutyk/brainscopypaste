#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from warnings import warn

from numpy import array
import pylab as pl

import datainterface.picklesaver as ps
from analyze.memetracker import build_timebag_transitions
import visualize.annotations as an
import settings as st


if __name__ == '__main__':
    base_prefix = 'F{ff}_{lem}L_P{pos}_{ntb}_{b1}-{b2}_'
    N = {0: 'N', 1: ''}
    
    parameters = []
    parameters_d = []
    
    wn_PR_scores_a = []
    wn_PR_scores_r_avgs = []
    wn_PR_scores_r_stds = []
    wn_PR_scores_r_lens = []
    wn_degrees_a = []
    wn_degrees_r_avgs = []
    wn_degrees_r_stds = []
    wn_degrees_r_lens = []
    fa_PR_scores_a = []
    fa_PR_scores_r_avgs = []
    fa_PR_scores_r_stds = []
    fa_PR_scores_r_lens = []
    
    for ff in ['full', 'framed', 'filtered', 'ff']:
        
        for lemmatizing in [0, 1]:
            
            for pos in st.memetracker_subst_POSs:
                
                for n_timebags in [2, 3, 4, 5]:
                    
                    for (b1, b2) in build_timebag_transitions(n_timebags):
                        
                        # Create the corresponding file names.
                        
                        file_prefix = base_prefix.format(ff=ff,
                                                         lem=N[lemmatizing],
                                                         pos=pos,
                                                         ntb=n_timebags,
                                                         b1=b1,
                                                         b2=b2)
                        pickle_wn_PR_scores = \
                            st.memetracker_subst_wn_PR_scores_pickle.\
                            format(file_prefix)
                        pickle_wn_degrees = \
                            st.memetracker_subst_wn_degrees_pickle.\
                            format(file_prefix)
                        pickle_fa_PR_scores = \
                            st.memetracker_subst_fa_PR_scores_pickle.\
                            format(file_prefix)
                        
                        # Load the data.
                        
                        try:
                            
                            wn_PR_scores = ps.load(pickle_wn_PR_scores)
                            wn_degrees = ps.load(pickle_wn_degrees)
                            fa_PR_scores = ps.load(pickle_fa_PR_scores)
                        
                        except IOError:
                            warn(("Files for parameters '{}' "
                                  'not found.').format(file_prefix))
                            continue
                        
                        if (len(wn_PR_scores) == 0 or
                            len(wn_degrees) == 0 or
                            len(fa_PR_scores) == 0):
                            warn(('There is some empty data for paramters '
                                  '{}.'.format(file_prefix)))
                            continue
                        
                        # Compute ratios and differences.
                        
                        wn_PR_scores_r = wn_PR_scores[:,1] / wn_PR_scores[:,0]
                        wn_degrees_r = wn_degrees[:,1] / wn_degrees[:,0]
                        fa_PR_scores_r = fa_PR_scores[:,1] / fa_PR_scores[:,0]
                        
                        # Store results.
                        
                        parameters.append(file_prefix[:-1])
                        parameters_d.append({'ff': ff,
                                             'lemmatizing': lemmatizing,
                                             'POS': pos,
                                             'n_timebags': n_timebags,
                                             'tr': (b1, b2)})
                        
                        wn_PR_scores_a.append(wn_PR_scores)
                        wn_PR_scores_r_avgs.append(wn_PR_scores_r.mean())
                        wn_PR_scores_r_stds.append(wn_PR_scores_r.std())
                        wn_PR_scores_r_lens.append(len(wn_PR_scores_r))
                        wn_degrees_a.append(wn_degrees)
                        wn_degrees_r_avgs.append(wn_degrees_r.mean())
                        wn_degrees_r_stds.append(wn_degrees_r.std())
                        wn_degrees_r_lens.append(len(wn_degrees_r))
                        fa_PR_scores_a.append(fa_PR_scores)
                        fa_PR_scores_r_avgs.append(fa_PR_scores_r.mean())
                        fa_PR_scores_r_stds.append(fa_PR_scores_r.std())
                        fa_PR_scores_r_lens.append(len(fa_PR_scores_r))
    
    
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
    
    
    # Build annotations
    
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
    
    def plotter(ax_tuple, annotedict):
        ax1, ax2 = ax_tuple
        
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
    
    
    # Plot everything
    
    fig_wn_sra = pl.figure()
    ax = pl.subplot(211)
    l_wn_sra = len(wn_PR_scores_r_avgs)
    pl.plot(wn_PR_scores_r_avgs, 'b-', linewidth=2)
    pl.plot(pl.ones(l_wn_sra), 'g--')
    pl.plot(wn_PR_scores_r_avgs - wn_PR_scores_r_ics, 'm-', linewidth=1)
    pl.plot(wn_PR_scores_r_avgs + wn_PR_scores_r_ics, 'm-', linewidth=1)
    pl.plot(wn_PR_scores_r_avgs, 'bo', linewidth=2)
    pl.plot(wn_PR_scores_r_avgs - wn_PR_scores_r_ics, 'm.', linewidth=1)
    pl.plot(wn_PR_scores_r_avgs + wn_PR_scores_r_ics, 'm.', linewidth=1)
    pl.legend(['averages', '1', 'av +/- IC-95%'])
    pl.title('WN PR scores ratio')
    
    ax.set_xticks(range(l_wn_sra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    af_wn_sra = an.AnnoteFinder(pl.arange(l_wn_sra), wn_PR_scores_r_avgs,
                                annotes, ytol=0.5)
    af2_wn_sra_ax1 = pl.subplot(223)
    af2_wn_sra_ax2 = pl.subplot(224)
    af2_wn_sra = an.AnnoteFinderPlot(wn_PR_annotes, fig_wn_sra,
                                     (af2_wn_sra_ax1, af2_wn_sra_ax2),
                                     plotter)
    pl.connect('button_press_event', af_wn_sra)
    
    
    fig_wn_dra = pl.figure()
    ax = pl.subplot(211)
    l_wn_dra = len(wn_degrees_r_avgs)
    pl.plot(wn_degrees_r_avgs, 'b-', linewidth=2)
    pl.plot(pl.ones(l_wn_dra), 'g--')
    pl.plot(wn_degrees_r_avgs - wn_degrees_r_ics, 'm-', linewidth=1)
    pl.plot(wn_degrees_r_avgs + wn_degrees_r_ics, 'm-', linewidth=1)
    pl.plot(wn_degrees_r_avgs, 'bo', linewidth=2)
    pl.plot(wn_degrees_r_avgs - wn_degrees_r_ics, 'm.', linewidth=1)
    pl.plot(wn_degrees_r_avgs + wn_degrees_r_ics, 'm.', linewidth=1)
    pl.legend(['averages', '1', 'av +/- IC-95%'])
    pl.title('WN Degrees ratio')
    
    ax.set_xticks(range(l_wn_dra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    af_wn_dra = an.AnnoteFinder(pl.arange(l_wn_dra), wn_degrees_r_avgs,
                                annotes, ytol=0.5)
    af2_wn_dra_ax1 = pl.subplot(223)
    af2_wn_dra_ax2 = pl.subplot(224)
    af2_wn_dra = an.AnnoteFinderPlot(wn_DEG_annotes, fig_wn_dra,
                                     (af2_wn_dra_ax1, af2_wn_dra_ax2),
                                     plotter)
    pl.connect('button_press_event', af_wn_dra)
    
    
    fig_fa_sra = pl.figure()
    ax = pl.subplot(211)
    l_fa_sra = len(fa_PR_scores_r_avgs)
    pl.plot(fa_PR_scores_r_avgs, 'b-', linewidth=2)
    pl.plot(pl.ones(l_fa_sra), 'g--')
    pl.plot(fa_PR_scores_r_avgs - fa_PR_scores_r_ics, 'm-', linewidth=1)
    pl.plot(fa_PR_scores_r_avgs + fa_PR_scores_r_ics, 'm-', linewidth=1)
    pl.plot(fa_PR_scores_r_avgs, 'bo', linewidth=2)
    pl.plot(fa_PR_scores_r_avgs - fa_PR_scores_r_ics, 'm.', linewidth=1)
    pl.plot(fa_PR_scores_r_avgs + fa_PR_scores_r_ics, 'm.', linewidth=1)
    pl.legend(['averages', '1', 'av +/- IC-95%'])
    pl.title('FA PR scores ratio')
    
    ax.set_xticks(range(l_fa_sra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    af_fa_sra = an.AnnoteFinder(pl.arange(l_fa_sra), fa_PR_scores_r_avgs,
                                annotes, ytol=0.5)
    af2_fa_sra_ax1 = pl.subplot(223)
    af2_fa_sra_ax2 = pl.subplot(224)
    af2_fa_sra = an.AnnoteFinderPlot(fa_PR_annotes, fig_fa_sra,
                                     (af2_fa_sra_ax1, af2_fa_sra_ax2),
                                     plotter)
    pl.connect('button_press_event', af_fa_sra)
    
    
    an.linkAnnotationFinders([af_wn_sra, af_fa_sra, af_wn_dra])
    af_wn_sra.links.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
    af_wn_dra.links.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
    af_fa_sra.links.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
    pl.show()
