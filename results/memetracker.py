#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools for working on results of substitution analysis of the MemeTracker
dataset.

"""


from __future__ import division

from warnings import warn

from numpy import array
import pylab as pl
import matplotlib.cm as cm

import datainterface.picklesaver as ps
from analyze.memetracker import SubstitutionAnalysis
import visualize.annotations as an
import settings as st


def list_to_dict(l):
    """Convert a list of items to a dict associating each single item to an
    array of its coordinates."""
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
    """Get the coordinates of clusters in a list of details of results."""
    return list_to_dict([detail['mother'].cl_id for detail in details])


def cl_means(values, clids):
    """Compute the means of values for clusters in a list, using provided
    grouping of values according to cluster ids."""
    means = []
    
    for idx in clids.itervalues():
        means.append(values[idx].mean())
    
    return array(means)


def plot_substseries(h0, r_avgs, r_ics, r_clids, annotes,
                       title, POS_series, ff_series, parameters_d):
    """Plot a dataseries resulting from the substitution analysis."""
    cmap = cm.jet
    n_POSs = len(st.memetracker_subst_POSs)
    col_POS = dict([(pos, cmap(i / n_POSs, alpha=0.3))
                    for i, pos in enumerate(st.memetracker_subst_POSs)])
    cmap = cm.winter
    col_ff = {'filtered': cmap(0.2, alpha=0.5), 'ff': cmap(0.6, alpha=0.5)}
    hatch_ff = {'filtered': '/', 'ff': '\\'}
    
    fig = pl.figure()
    ax = pl.subplot(111)
    #ax = pl.subplot(211)
    l = len(r_avgs)
    
    xleft, xright = - 0.5, l - 0.5
    yrange = pl.amax(r_avgs + r_ics) - pl.amin(r_avgs - r_ics)
    ybot, ytop2 = 1 - yrange / 5, pl.amax(r_avgs + r_ics) + yrange / 5
    ytop0 = ytop2 - (ytop2 - ybot) * 0.1
    ytop1 = ytop2 - (ytop2 - ybot) * 0.05
    ytop3 = ytop2 + (ytop2 - ybot) * 0.05
    ytop4 = ytop2 + (ytop2 - ybot) * 0.1
    
    setlabel = True
    for pos, xpos in POS_series:
        
        lbl = 'H0' if setlabel else None
        setlabel = False
        pl.plot([min(xpos) - 0.5, max(xpos) + 0.5], [h0[pos], h0[pos]], 'k--',
                linewidth=2, label=lbl)
        pl.fill_between([min(xpos) - 0.5, max(xpos) + 0.5], ytop2, ybot,
                        color=col_POS[pos], edgecolor=(0, 0, 0, 0))
        pl.text((min(xpos) + max(xpos)) / 2, ytop1, pos,
                bbox=dict(facecolor='white', edgecolor='white', alpha=0.8),
                ha='center', va='center')
    
    setlabel = True
    for i in range(len(r_avgs)):
        
        # The real results
        
        lbl = 'averages' if setlabel else None
        pl.plot(i, r_avgs[i], 'bo', linewidth=3, label=lbl)
        lbl = 'avgs +/- IC-95%' if setlabel else None
        pl.plot(i, r_avgs[i] - r_ics[i], 'm.', linewidth=2, label=lbl)
        setlabel = False
        pl.plot(i, r_avgs[i] + r_ics[i], 'm.', linewidth=2)
        
        # The vertical lines and text
        
        pl.plot([i - 0.5, i - 0.5], [ybot, ytop0], color=(0.5, 0.5, 0.5, 0.3))
        pl.plot([i + 0.5, i + 0.5], [ybot, ytop0], color=(0.5, 0.5, 0.5, 0.3))
        if parameters_d[i]['n_timebags'] != 0:
            pl.text(i, ytop0, '{}'.format(parameters_d[i]['n_timebags']),
                    bbox=dict(facecolor='white', edgecolor='white',
                              alpha=0.8),
                    ha='center', va='center')
    
    for ff, xff in ff_series:
        
        pl.fill([xff[0] - 0.5, xff[0] - 0.5, xff[-1] + 0.5, xff[-1] + 0.5],
                [ytop4, ytop2, ytop2, ytop4], color=col_ff[ff],
                edgecolor = (0, 0, 0, 0), hatch=hatch_ff[ff])
        pl.text((min(xff) + max(xff)) / 2, ytop3, ff,
                bbox=dict(facecolor='white', edgecolor='white', alpha=0.8),
                ha='center', va='center')
    
    ax.set_xlim(xleft, xright)
    ax.set_ylim(ybot, ytop4)
    pl.legend(loc='best', prop=dict(size='small'))
    pl.title(title)
    
    ax.set_xticks(range(l))
    labels = ax.set_xticklabels(['{}'.format(p['n_timebags'])
                                 for p in parameters_d
                                 if p['n_timebags'] != 0])
    pl.setp(labels, rotation=60, fontsize=10)
    
    af = an.AnnoteFinder(pl.arange(l), r_avgs, annotes, ytol=0.5)
    pl.connect('button_press_event', af)
#    af2_ax1 = pl.subplot(223)
#    af2_ax2 = pl.subplot(224)
#    af2 = an.AnnoteFinderPlot(wn_PR_annotes, fig, [af2_ax1, af2_ax2],
#                              plotter)
#    
#    return (af, af2)
    return (af, None)


class DictNS(object):
    
    """A dummy class to turn a dict into a namespace."""
    
    def __init__(self, d):
        self.__dict__.update(d)


def iter_all_results(args):
    """Iterate through all substitution analysis results."""
    sa = SubstitutionAnalysis()
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
        
        yield argset, {'wn_PR_scores': wn_PR_scores,
                       'wn_PR_scores_d': wn_PR_scores_d,
                       'wn_degrees': wn_degrees,
                       'wn_degrees_d': wn_degrees_d,
                       'fa_PR_scores': fa_PR_scores,
                       'fa_PR_scores_d': fa_PR_scores_d}
