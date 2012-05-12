#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from warnings import warn

from numpy import array
import pylab as pl

import datainterface.picklesaver as ps
from analyze.memetracker import build_timebag_transitions
from visualize.annotations import AnnoteFinder, linkAnnotationFinders
import settings as st


if __name__ == '__main__':
    base_prefix = 'F{ff}_{lem}L_P{pos}_{ntb}_{b1}-{b2}_'
    N = {0: 'N', 1: ''}
    
    parameters = []
    
    wn_PR_scores_r_avgs = []
    wn_PR_scores_r_stds = []
    wn_PR_scores_r_lens = []
    wn_degrees_r_avgs = []
    wn_degrees_r_stds = []
    wn_degrees_r_lens = []
    fa_PR_scores_r_avgs = []
    fa_PR_scores_r_stds = []
    fa_PR_scores_r_lens = []
    
    for ff in ['full', 'framed', 'filtered', 'ff']:
        
        for lemmatizing in [0, 1]:
            
            for pos in st.memetracker_subst_POSs:
                
                for n_timebags in [2, 3, 4, 5]:
                    
                    for (b1, b2) in build_timebag_transitions(n_timebags):
                        
                        # Create the corresponding file names.
                        
                        file_prefix = base_prefix.format(ff=N[ff],
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
                        
                        except:
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
                        
                        wn_PR_scores_r_avgs.append(wn_PR_scores_r.mean())
                        wn_PR_scores_r_stds.append(wn_PR_scores_r.std())
                        wn_PR_scores_r_lens.append(len(wn_PR_scores_r))
                        wn_degrees_r_avgs.append(wn_degrees_r.mean())
                        wn_degrees_r_stds.append(wn_degrees_r.std())
                        wn_degrees_r_lens.append(len(wn_degrees_r))
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
    
    
    # Plot it all, with annotations.
    
    annotes = ['wn_PR: {}\nwn_deg: {}\nfa_PR: {}'.format(n_wn_PR, n_wn_deg,
                                                         n_fa_PR)
               for (n_wn_PR, n_wn_deg, n_fa_PR) in zip(wn_PR_scores_r_lens,
                                                       wn_degrees_r_lens,
                                                       fa_PR_scores_r_lens)]
    
    pl.figure()
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
    
    af_wn_sra = AnnoteFinder(pl.arange(l_wn_sra), wn_PR_scores_r_avgs,
                             annotes)
    pl.connect('button_press_event', af_wn_sra)
    
    ax = pl.gca()
    ax.set_xticks(range(l_wn_sra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    
    pl.figure()
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
    
    af_wn_dra = AnnoteFinder(pl.arange(l_wn_dra), wn_degrees_r_avgs, annotes)
    pl.connect('button_press_event', af_wn_dra)
    
    ax = pl.gca()
    ax.set_xticks(range(l_wn_dra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    
    pl.figure()
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
    
    af_fa_sra = AnnoteFinder(pl.arange(l_fa_sra),
                             fa_PR_scores_r_avgs, annotes)
    pl.connect('button_press_event', af_fa_sra)
    
    ax = pl.gca()
    ax.set_xticks(range(l_fa_sra))
    labels = ax.set_xticklabels(parameters)
    pl.setp(labels, rotation=30, fontsize=10)
    
    
    linkAnnotationFinders([af_wn_sra, af_fa_sra, af_wn_dra])    
    pl.show()
