#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from warnings import warn

from numpy import median, array, argsort
import pylab as pl

import datainterface.picklesaver as ps
from analyze.memetracker import build_timebag_transitions
import settings as st


if __name__ == '__main__':
    base_prefix = '{fra}F_{lem}L_{pos}P_{ntb}_{b1}-{b2}_'
    N = {0: 'N', 1: ''}
    
    parameters = []
    
    wn_PR_scores_r_avgs = []
    wn_PR_scores_r_stds = []
    wn_PR_scores_r_meds = []
    wn_degrees_r_avgs = []
    wn_degrees_r_stds = []
    wn_degrees_r_meds = []
    fa_PR_scores_r_avgs = []
    fa_PR_scores_r_stds = []
    fa_PR_scores_r_meds = []
    
    wn_PR_scores_d_avgs = []
    wn_PR_scores_d_stds = []
    wn_PR_scores_d_meds = []
    wn_degrees_d_avgs = []
    wn_degrees_d_stds = []
    wn_degrees_d_meds = []
    fa_PR_scores_d_avgs = []
    fa_PR_scores_d_stds = []
    fa_PR_scores_d_meds = []
    
    for framing in [1]:#[0, 1]:
        
        for lemmatizing in [1]:#[0, 1]:
            
            for same_POS in [1]:#[0, 1]:
                
                for n_timebags in [2, 3, 4, 5]:
                    
                    for (b1, b2) in build_timebag_transitions(n_timebags):
                        
                        # Create the corresponding file names.
                        
                        file_prefix = base_prefix.format(fra=N[framing],
                                                         lem=N[lemmatizing],
                                                         pos=N[same_POS],
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
                            break
                        
                        # Compute ratios and differences.
                        
                        wn_PR_scores_r = wn_PR_scores[:,1] / wn_PR_scores[:,0]
                        wn_degrees_r = wn_degrees[:,1] / wn_degrees[:,0]
                        fa_PR_scores_r = fa_PR_scores[:,1] / fa_PR_scores[:,0]
                        wn_PR_scores_d = wn_PR_scores[:,1] - wn_PR_scores[:,0]
                        wn_degrees_d = wn_degrees[:,1] - wn_degrees[:,0]
                        fa_PR_scores_d = fa_PR_scores[:,1] - fa_PR_scores[:,0]
                        
                        # Store results.
                        
                        parameters.append(file_prefix[:-1])
                        
#                        w = pl.where(abs(wn_PR_scores_r -
#                                         wn_PR_scores_r.mean()) <
#                                     wn_PR_scores_r.std())
                        
#                        wn_PR_scores_r_avgs.append(wn_PR_scores_r[w].mean())
#                        wn_PR_scores_r_stds.append(wn_PR_scores_r[w].std())
#                        wn_PR_scores_r_meds.append(median(wn_PR_scores_r[w]))
                        wn_PR_scores_r_avgs.append(wn_PR_scores_r.mean())
                        wn_PR_scores_r_stds.append(wn_PR_scores_r.std())
                        wn_PR_scores_r_meds.append(median(wn_PR_scores_r))
                        wn_degrees_r_avgs.append(wn_degrees_r.mean())
                        wn_degrees_r_stds.append(wn_degrees_r.std())
                        wn_degrees_r_meds.append(median(wn_degrees_r))
                        fa_PR_scores_r_avgs.append(fa_PR_scores_r.mean())
                        fa_PR_scores_r_stds.append(fa_PR_scores_r.std())
                        fa_PR_scores_r_meds.append(median(fa_PR_scores_r))
                        
                        wn_PR_scores_d_avgs.append(wn_PR_scores_d.mean())
                        wn_PR_scores_d_stds.append(wn_PR_scores_d.std())
                        wn_PR_scores_d_meds.append(median(wn_PR_scores_d))
                        wn_degrees_d_avgs.append(wn_degrees_d.mean())
                        wn_degrees_d_stds.append(wn_degrees_d.std())
                        wn_degrees_d_meds.append(median(wn_degrees_d))
                        fa_PR_scores_d_avgs.append(fa_PR_scores_d.mean())
                        fa_PR_scores_d_stds.append(fa_PR_scores_d.std())
                        fa_PR_scores_d_meds.append(median(fa_PR_scores_d))
    
    
    # Convert the results to Numpy arrays.
    
    wn_PR_scores_r_avgs = array(wn_PR_scores_r_avgs)
    wn_PR_scores_r_stds = array(wn_PR_scores_r_stds)
    wn_PR_scores_r_meds = array(wn_PR_scores_r_meds)
    wn_degrees_r_avgs = array(wn_degrees_r_avgs)
    wn_degrees_r_stds = array(wn_degrees_r_stds)
    wn_degrees_r_meds = array(wn_degrees_r_meds)
    fa_PR_scores_r_avgs = array(fa_PR_scores_r_avgs)
    fa_PR_scores_r_stds = array(fa_PR_scores_r_stds)
    fa_PR_scores_r_meds = array(fa_PR_scores_r_meds)
    
    wn_PR_scores_d_avgs = array(wn_PR_scores_d_avgs)
    wn_PR_scores_d_stds = array(wn_PR_scores_d_stds)
    wn_PR_scores_d_meds = array(wn_PR_scores_d_meds)
    wn_degrees_d_avgs = array(wn_degrees_d_avgs)
    wn_degrees_d_stds = array(wn_degrees_d_stds)
    wn_degrees_d_meds = array(wn_degrees_d_meds)
    fa_PR_scores_d_avgs = array(fa_PR_scores_d_avgs)
    fa_PR_scores_d_stds = array(fa_PR_scores_d_stds)
    fa_PR_scores_d_meds = array(fa_PR_scores_d_meds)
    
    
    # Plot it all.
    
    pl.figure()
    o_wn_sra = argsort(wn_PR_scores_r_avgs)
    pl.plot(wn_PR_scores_r_avgs[o_wn_sra], 'b-', linewidth=2)
    pl.plot(wn_PR_scores_r_meds[o_wn_sra], 'g--', linewidth=2)
    pl.plot(wn_PR_scores_r_avgs[o_wn_sra] - wn_PR_scores_r_stds[o_wn_sra],
            'm-', linewidth=1)
    pl.plot(wn_PR_scores_r_avgs[o_wn_sra] + wn_PR_scores_r_stds[o_wn_sra],
            'm-', linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('WN PR scores ratio (sorted by increasing average)')
    
    print
    print 'WN PR scores ratio -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_wn_sra[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_wn_dra = argsort(wn_degrees_r_avgs)
    pl.plot(wn_degrees_r_avgs[o_wn_dra], 'b-', linewidth=2)
    pl.plot(wn_degrees_r_meds[o_wn_dra], 'g--', linewidth=2)
    pl.plot(wn_degrees_r_avgs[o_wn_dra] - wn_degrees_r_stds[o_wn_dra], 'm-',
            linewidth=1)
    pl.plot(wn_degrees_r_avgs[o_wn_dra] + wn_degrees_r_stds[o_wn_dra], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('WN Degrees ratio (sorted by increasing average)')
    
    print
    print 'WN Degrees ratio -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_wn_dra[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_fa_sra = argsort(fa_PR_scores_r_avgs)
    pl.plot(fa_PR_scores_r_avgs[o_fa_sra], 'b-', linewidth=2)
    pl.plot(fa_PR_scores_r_meds[o_fa_sra], 'g--', linewidth=2)
    pl.plot(fa_PR_scores_r_avgs[o_fa_sra] - fa_PR_scores_r_stds[o_fa_sra],
            'm-', linewidth=1)
    pl.plot(fa_PR_scores_r_avgs[o_fa_sra] + fa_PR_scores_r_stds[o_fa_sra],
            'm-', linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('FA PR scores ratio (sorted by increasing average)')
    
    print
    print 'FA PR scores ratio -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_fa_sra[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_wn_sda = argsort(wn_PR_scores_d_avgs)
    pl.plot(wn_PR_scores_d_avgs[o_wn_sda], 'b-', linewidth=2)
    pl.plot(wn_PR_scores_d_meds[o_wn_sda], 'g--', linewidth=2)
    pl.plot(wn_PR_scores_d_avgs[o_wn_sda] - wn_PR_scores_d_stds[o_wn_sda],
            'm-', linewidth=1)
    pl.plot(wn_PR_scores_d_avgs[o_wn_sda] + wn_PR_scores_d_stds[o_wn_sda],
            'm-', linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('WN PR scores diff (sorted by increasing average)')
    
    print
    print 'WN PR scores diff -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_wn_sda[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_wn_dda = argsort(wn_degrees_d_avgs)
    pl.plot(wn_degrees_d_avgs[o_wn_dda], 'b-', linewidth=2)
    pl.plot(wn_degrees_d_meds[o_wn_dda], 'g--', linewidth=2)
    pl.plot(wn_degrees_d_avgs[o_wn_dda] - wn_degrees_d_stds[o_wn_dda], 'm-',
            linewidth=1)
    pl.plot(wn_degrees_d_avgs[o_wn_dda] + wn_degrees_d_stds[o_wn_dda], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('WN Degrees diff (sorted by increasing average)')
    
    print
    print 'WN Degrees diff -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_wn_dda[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_fa_sda = argsort(fa_PR_scores_d_avgs)
    pl.plot(fa_PR_scores_d_avgs[o_fa_sda], 'b-', linewidth=2)
    pl.plot(fa_PR_scores_d_meds[o_fa_sda], 'g--', linewidth=2)
    pl.plot(fa_PR_scores_d_avgs[o_fa_sda] - fa_PR_scores_d_stds[o_fa_sda],
            'm-', linewidth=1)
    pl.plot(fa_PR_scores_d_avgs[o_fa_sda] + fa_PR_scores_d_stds[o_fa_sda],
            'm-', linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('FA PR scores diff (sorted by increasing average)')
    
    print
    print 'FA PR scores diff -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_fa_sda[i]]) for i in
                     range(len(parameters))])
    
    pl.show()
