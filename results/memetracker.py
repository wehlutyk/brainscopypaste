#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools for working on results of substitution analysis of the MemeTracker
dataset.

Methods:
  * list_to_dict: convert a list of items to a dict associating each single
                  item to an array of its coordinates
  * plot_substseries: plot a dataseries resulting from the substitution
                      analysis
  * iter_results_all: iterate through all substitution analysis results
                      corresponding to given args
  * load_feature_values: get the lists of values of the features. Returns a
                         dict (for feature names) of dicts (for POS) of
                         arrays.

Classes:
  * DictNS: a dummy class to turn a dict into a namespace
  * ArgsetResults: hold results of substitution analysis for one argset and
                   one type of feature

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
    
    pl.figure()
    ax = pl.subplot(111)
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
    
    return af


class DictNS(object):
    
    """A dummy class to turn a dict into a namespace."""
    
    def __init__(self, d):
        self.__dict__.update(d)


class ArgsetResults(object):
    
    """Hold results of substitution analysis for one argset and one type of
    feature.
    
    Methods:
      * __init__: initialize the structure with data and details about the
                  data, as resulting from a substitution analysis
      * clmeans: compute the means of a list of values, grouped by clusters
    
    """
    
    def __init__(self, data, details):
        """Initialize the structure with data and details about the data, as
        resulting from a substitution analysis."""
        self.length = len(data[:, 0])
        
        if self.length <= 1:
            return None
        
        self.data = data
        self.details = details
        
        # Get the coordinates of clusters in the list of details of results.
        
        self.clids = list_to_dict([detail['mother'].cl_id
                                   for detail in self.details])
        
        # Compute ratios, correct them to represent the means
        # by clusters.
        
        self.ratios = data[:, 1] / data[:, 0]
        self.cl_ratios = self.clmeans(self.ratios)
    
    def clmeans(self, values):
        """Compute the means of a list of values, grouped by clusters."""
        means = []
        
        for idx in self.clids.itervalues():
            means.append(values[idx].mean())
        
        return array(means)


def iter_results_all(args):
    """Iterate through all substitution analysis results corresponding to
    given args."""
    sa = SubstitutionAnalysis()
    argsets = sa.create_argsets(args)
    
    for argset in argsets:
        
        # Load the data.
        
        pickle_files = sa.get_save_files(argset, readonly=True)
        
        if pickle_files == None:
            continue
        
        wn_PR_scores = ArgsetResults(ps.load(pickle_files['wn_PR_scores']),
                                    ps.load(pickle_files['wn_PR_scores_d']))
        wn_degrees = ArgsetResults(ps.load(pickle_files['wn_degrees']),
                                  ps.load(pickle_files['wn_degrees_d']))
        fa_PR_scores = ArgsetResults(ps.load(pickle_files['fa_PR_scores']),
                                    ps.load(pickle_files['fa_PR_scores_d']))
        
        if (wn_PR_scores == None or wn_degrees == None or
            fa_PR_scores.length == None):
            warn('{}: empty data'.format(argset))
            continue
        
        yield argset, {'wn_PR_scores': wn_PR_scores,
                       'wn_degrees': wn_degrees,
                       'fa_PR_scores': fa_PR_scores,}


def load_feature_values():
    """Get the lists of values of the features. Returns a dict (for feature
    names) of dicts (for POS) of arrays."""
    wn_PR_scores_v = {}
    wn_degrees_v = {}
    
    for pos in st.memetracker_subst_POSs:
        
        wn_PR_scores = ps.load(st.wordnet_PR_scores_pickle.format(pos))
        wn_degrees = ps.load(st.wordnet_degrees_pickle.format(pos))
        wn_PR_scores_v[pos] = array(wn_PR_scores.values())
        wn_degrees_v[pos] = array(wn_degrees.values())
    
    fa_PR_scores = ps.load(st.freeassociation_norms_PR_scores_pickle)
    fa_PR_scores_v0 = array(fa_PR_scores.values())
    fa_PR_scores_v = dict([(pos, fa_PR_scores_v0)
                           for pos in st.memetracker_subst_POSs])
    
    return {'wn_PR_scores': wn_PR_scores_v, 'wn_degrees': wn_degrees_v,
            'fa_PR_scores': fa_PR_scores_v}
