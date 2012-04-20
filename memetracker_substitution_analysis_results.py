#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from numpy import median, array, argsort
import pylab as pl

import datainterface.picklesaver as ps
from analyze.memetracker import build_timebag_transitions
import settings as st


if __name__ == '__main__':
    base_prefix = '{fra}F_{lem}L_{pos}P_{ntb}_{b1}-{b2}_'
    N = {0: 'N', 1: ''}
    
    parameters = []
    
    degrees_ratio_averages = []
    degrees_ratio_stds = []
    degrees_ratio_medians = []
    PRscores_ratio_averages = []
    PRscores_ratio_stds = []
    PRscores_ratio_medians = []
    
    degrees_diff_averages = []
    degrees_diff_stds = []
    degrees_diff_medians = []
    PRscores_diff_averages = []
    PRscores_diff_stds = []
    PRscores_diff_medians = []
    
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
                        pickle_transitiondegrees = \
                            st.memetracker_subst_transitiondegrees_pickle.\
                            format(file_prefix)
                        pickle_transitionPRscores = \
                            st.memetracker_subst_transitionPRscores_pickle.\
                            format(file_prefix)
                        
                        # Load the data.
                        
                        degrees = ps.load(pickle_transitiondegrees)
                        PRscores = ps.load(pickle_transitionPRscores)
                        
                        # Compute ratios and differences.
                        
                        degrees_ratio = degrees[:,1] / degrees[:,0]
                        PRscores_ratio = PRscores[:,1] / PRscores[:,0]
                        degrees_diff = degrees[:,1] - degrees[:,0]
                        PRscores_diff = PRscores[:,1] - PRscores[:,0]
                        
                        # Store results.
                        
                        parameters.append(file_prefix[:-1])
                        
#                        w = pl.where(abs(PRscores_ratio -
#                                         PRscores_ratio.mean()) <
#                                     PRscores_ratio.std())
                        
                        degrees_ratio_averages.append(degrees_ratio.mean())
                        degrees_ratio_stds.append(degrees_ratio.std())
                        degrees_ratio_medians.append(median(degrees_ratio))
#                        PRscores_ratio_averages.append(PRscores_ratio[w].mean())
#                        PRscores_ratio_stds.append(PRscores_ratio[w].std())
#                        PRscores_ratio_medians.append(median(PRscores_ratio[w]))
                        PRscores_ratio_averages.append(PRscores_ratio.mean())
                        PRscores_ratio_stds.append(PRscores_ratio.std())
                        PRscores_ratio_medians.append(median(PRscores_ratio))
                        
                        degrees_diff_averages.append(degrees_diff.mean())
                        degrees_diff_stds.append(degrees_diff.std())
                        degrees_diff_medians.append(median(degrees_diff))
                        PRscores_diff_averages.append(PRscores_diff.mean())
                        PRscores_diff_stds.append(PRscores_diff.std())
                        PRscores_diff_medians.append(median(PRscores_diff))
    
    
    # Convert the results to Numpy arrays.
    
    degrees_ratio_averages = array(degrees_ratio_averages)
    degrees_ratio_stds = array(degrees_ratio_stds)
    degrees_ratio_medians = array(degrees_ratio_medians)
    PRscores_ratio_averages = array(PRscores_ratio_averages)
    PRscores_ratio_stds = array(PRscores_ratio_stds)
    PRscores_ratio_medians = array(PRscores_ratio_medians)
    
    degrees_diff_averages = array(degrees_diff_averages)
    degrees_diff_stds = array(degrees_diff_stds)
    degrees_diff_medians = array(degrees_diff_medians)
    PRscores_diff_averages = array(PRscores_diff_averages)
    PRscores_diff_stds = array(PRscores_diff_stds)
    PRscores_diff_medians = array(PRscores_diff_medians)
    
    
    # Plot it all.
    
    pl.figure()
    o_dra = argsort(degrees_ratio_averages)
    pl.plot(degrees_ratio_averages[o_dra], 'b-', linewidth=2)
    pl.plot(degrees_ratio_medians[o_dra], 'g--', linewidth=2)
    pl.plot(degrees_ratio_averages[o_dra] - degrees_ratio_stds[o_dra], 'm-',
            linewidth=1)
    pl.plot(degrees_ratio_averages[o_dra] + degrees_ratio_stds[o_dra], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('Degrees ratio (sorted by increasing average)')
    
    print
    print 'Degrees ratio -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_dra[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_sra = argsort(PRscores_ratio_averages)
    pl.plot(PRscores_ratio_averages[o_sra], 'b-', linewidth=2)
    pl.plot(PRscores_ratio_medians[o_sra], 'g--', linewidth=2)
    pl.plot(PRscores_ratio_averages[o_sra] - PRscores_ratio_stds[o_sra], 'm-',
            linewidth=1)
    pl.plot(PRscores_ratio_averages[o_sra] + PRscores_ratio_stds[o_sra], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('PRscores ratio (sorted by increasing average)')
    
    print
    print 'PRscores ratio -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_sra[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_dda = argsort(degrees_diff_averages)
    pl.plot(degrees_diff_averages[o_dda], 'b-', linewidth=2)
    pl.plot(degrees_diff_medians[o_dda], 'g--', linewidth=2)
    pl.plot(degrees_diff_averages[o_dda] - degrees_diff_stds[o_dda], 'm-',
            linewidth=1)
    pl.plot(degrees_diff_averages[o_dda] + degrees_diff_stds[o_dda], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('Degrees diff (sorted by increasing average)')
    
    print
    print 'Degrees diff -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_dda[i]]) for i in
                     range(len(parameters))])
    
    pl.figure()
    o_sda = argsort(PRscores_diff_averages)
    pl.plot(PRscores_diff_averages[o_sda], 'b-', linewidth=2)
    pl.plot(PRscores_diff_medians[o_sda], 'g--', linewidth=2)
    pl.plot(PRscores_diff_averages[o_sda] - PRscores_diff_stds[o_sda], 'm-',
            linewidth=1)
    pl.plot(PRscores_diff_averages[o_sda] + PRscores_diff_stds[o_sda], 'm-',
            linewidth=1)
    pl.legend(['averages', 'medians', 'av +/- std'])
    pl.title('PRscores diff (sorted by increasing average)')
    
    print
    print 'PRscores diff -- parameters ordering:'
    print '\n'.join(['{} - {}'.format(i, parameters[o_sda[i]]) for i in
                     range(len(parameters))])
    
    pl.show()
