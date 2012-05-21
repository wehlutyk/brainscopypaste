#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from __future__ import division

from warnings import warn

from numpy import array
import pylab as pl
import matplotlib.cm as cm

import datainterface.picklesaver as ps
from analyze.memetracker import build_timebag_transitions
import visualize.annotations as an
import settings as st


def list_to_dict(l):
    """Convert a list of items to a dict associating each item to an array of
    its coordinates."""
    out = {}
    
    for i, item in enumerate(l):
        
        if out.has_key(item):
            out[item].append(i)
        else:
            out[item] = [i]
    
    for k, v in out.iteritems():
        out[k] = array(v)
    
    return out


def clids(details):
    """Get the coordinates of clusters from a list of details of results."""
    return list_to_dict([detail['cl_id'] for detail in details])


def cl_means(values, clids):
    """Compute the means of values for clusters in a list, using provided
    grouping of values according to cluster ids."""
    means = []
    
    for idx in clids.itervalues():
        means.append(values[idx].mean())
    
    return array(means)


if __name__ == '__main__':
    base_prefix = 'F{ff}_{lem}L_P{pos}_{ntb}_{b1}-{b2}_'
    N = {0: 'N', 1: ''}
    cmap = cm.jet
    n_POSs = len(st.memetracker_subst_POSs)
    col_POS = dict([(pos, cmap(i / n_POSs, alpha=0.3))
                    for i, pos in enumerate(st.memetracker_subst_POSs)])
    cmap = cm.winter
    col_ff = {'filtered': cmap(0.2, alpha=0.5), 'ff': cmap(0.6, alpha=0.5)}
    hatch_ff = {'filtered': '/', 'ff': '\\'}
    
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
    
    for ff in ['filtered', 'ff']:#['full', 'framed', 'filtered', 'ff']:
        
        for lemmatizing in [1]:#[0, 1]:
            
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
                        pickle_wn_PR_scores_d = \
                            st.memetracker_subst_wn_PR_scores_d_pickle.\
                            format(file_prefix)
                        pickle_wn_degrees = \
                            st.memetracker_subst_wn_degrees_pickle.\
                            format(file_prefix)
                        pickle_wn_degrees_d = \
                            st.memetracker_subst_wn_degrees_d_pickle.\
                            format(file_prefix)
                        pickle_fa_PR_scores = \
                            st.memetracker_subst_fa_PR_scores_pickle.\
                            format(file_prefix)
                        pickle_fa_PR_scores_d = \
                            st.memetracker_subst_fa_PR_scores_d_pickle.\
                            format(file_prefix)
                        
                        # Load the data.
                        
                        try:
                            
                            wn_PR_scores = ps.load(pickle_wn_PR_scores)
                            wn_PR_scores_d = ps.load(pickle_wn_PR_scores_d)
                            wn_degrees = ps.load(pickle_wn_degrees)
                            wn_degrees_d = ps.load(pickle_wn_degrees_d)
                            fa_PR_scores = ps.load(pickle_fa_PR_scores)
                            fa_PR_scores_d = ps.load(pickle_fa_PR_scores_d)
                        
                        except IOError:
                            
                            warn('{}: not found'.format(file_prefix))
                            continue
                        
                        if (len(wn_PR_scores) == 0 or
                            len(wn_degrees) == 0 or
                            len(fa_PR_scores) == 0):
                            warn('{}: empty data'.format(file_prefix))
                            continue
                        
                        # Compute ratios, correct them to represent the means
                        # by clusters.
                        
                        wn_PR_scores_r = cl_means(wn_PR_scores[:,1] /
                                                  wn_PR_scores[:,0],
                                                  clids(wn_PR_scores_d))
                        wn_degrees_r = cl_means(wn_degrees[:,1] /
                                                wn_degrees[:,0],
                                                clids(wn_degrees_d))
                        fa_PR_scores_r = cl_means(fa_PR_scores[:,1] /
                                                  fa_PR_scores[:,0],
                                                  clids(fa_PR_scores_d))
                        
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
    
    def plotter(ax_list, annotedict):
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
    
    
    def plot_dataseries(r_avgs, r_ics, annotes, title):
        fig = pl.figure()
        ax = pl.subplot(111)
        #ax = pl.subplot(211)
        l = len(r_avgs)
        pl.plot(r_avgs, 'b-', linewidth=2)
        pl.plot(pl.ones(l), 'g--')
        pl.plot(r_avgs - r_ics, 'm-', linewidth=1)
        pl.plot(r_avgs + r_ics, 'm-', linewidth=1)
        pl.plot(r_avgs, 'bo', linewidth=2)
        pl.plot(r_avgs - r_ics, 'm.', linewidth=1)
        pl.plot(r_avgs + r_ics, 'm.', linewidth=1)
        
        ybot, ytop2 = ax.get_ylim()
        ytop0 = ytop2 - (ytop2 - ybot) * 0.1
        ytop1 = ytop2 - (ytop2 - ybot) * 0.05
        ytop3 = ytop2 + (ytop2 - ybot) * 0.05
        ytop4 = ytop2 + (ytop2 - ybot) * 0.1
        
        for pos, xpos in POS_series:
        
            pl.fill_between([min(xpos) - 0.5, max(xpos) + 0.5], ytop2, ybot,
                            color=col_POS[pos], edgecolor=(0, 0, 0, 0))
            pl.text((min(xpos) + max(xpos)) / 2, ytop1, pos,
                    bbox=dict(facecolor='white', edgecolor='white',
                              alpha=0.8),
                    ha='center', va='center')
        
        for ff, xff in ff_series:
            
            pl.fill([xff[0] - 0.5, xff[0] - 0.5,
                     xff[-1] + 0.5, xff[-1] + 0.5],
                    [ytop4, ytop2, ytop2, ytop4], color=col_ff[ff],
                    edgecolor = (0, 0, 0, 0), hatch=hatch_ff[ff])
            pl.text((min(xff) + max(xff)) / 2, ytop3, ff,
                    bbox=dict(facecolor='white', edgecolor='white',
                              alpha=0.8),
                    ha='center', va='center')
        
        for ntb, xntb in ntb_series:
            
            pl.plot([xntb[0] - 0.5, xntb[0] - 0.5], [ybot, ytop0],
                    color=(0.5, 0.5, 0.5, 0.3))
            pl.plot([xntb[-1] + 0.5, xntb[-1] + 0.5], [ybot, ytop0],
                    color=(0.5, 0.5, 0.5, 0.3))
            pl.text((min(xntb) + max(xntb)) / 2, ytop0, '{}'.format(ntb),
                    bbox=dict(facecolor='white', edgecolor='white',
                              alpha=0.8),
                    ha='center', va='center')
        
        ax.set_xlim(POS_series[0][1][0] - 0.5, POS_series[-1][1][-1] + 0.5)
        ax.set_ylim(ybot, ytop4)
        pl.legend(['averages', '1', 'av +/- IC-95%'])
        pl.title(title)
        
        ax.set_xticks(range(l))
        labels = ax.set_xticklabels(['{}: {}-{}'.format(p['n_timebags'],
                                                        p['tr'][0],
                                                        p['tr'][1])
                                     for p in parameters_d])
        pl.setp(labels, rotation=60, fontsize=10)
        
        af = an.AnnoteFinder(pl.arange(l), r_avgs,
                             annotes, ytol=0.5)
#        af2_ax1 = pl.subplot(223)
#        af2_ax2 = pl.subplot(224)
#        af2 = an.AnnoteFinderPlot(wn_PR_annotes, fig, [af2_ax1, af2_ax2],
#                                  plotter)
#        pl.connect('button_press_event', af)
#        
#        return (af, af2)
        return (af, None)
    
    
    # Plot everything
    
    af_wn_sra, af2_wn_sra = plot_dataseries(wn_PR_scores_r_avgs,
                                            wn_PR_scores_r_ics, wn_PR_annotes,
                                            'WN PR scores ratio')
    af_wn_dra, af2_wn_dra = plot_dataseries(wn_degrees_r_avgs,
                                            wn_degrees_r_ics, wn_DEG_annotes,
                                            'WN Degrees ratio')
    af_fa_sra, af2_fa_sra = plot_dataseries(fa_PR_scores_r_avgs,
                                            fa_PR_scores_r_ics, fa_PR_annotes,
                                            'FA PR scores ratio')
    
    an.linkAnnotationFinders([af_wn_sra, af_fa_sra, af_wn_dra])
#    af_wn_sra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
#    af_wn_dra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
#    af_fa_sra.plotlinks.extend([af2_wn_sra, af2_wn_dra, af2_fa_sra])
    pl.show()
