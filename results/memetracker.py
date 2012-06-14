#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools for working on results of substitution analysis of the MemeTracker
dataset.

Methods:
  * list_to_dict: convert a list of items to a dict associating each single
                  item to an array of its coordinates
  * plot_substseries: plot a dataseries resulting from the substitution
                      analysis
  * iter_argsets_results: iterate through all substitution analysis results
                      corresponding to given args
  * load_ratio_results: load all the results of substitution analysis
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
import visualize.annotations_new as an
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


def plot_substseries(h0, fv, r_avgs, r_ics, r_clids, annotes,
                       title, POS_series, ff_series, argsets):
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
        if argsets[i]['n_timebags'] != 0:
            pl.text(i, ytop0, '{}'.format(argsets[i]['n_timebags']),
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
                                 for p in argsets if p['n_timebags'] != 0])
    pl.setp(labels, rotation=60, fontsize=10)
    
    def formatter(an):
        return an['text']
    
    def side_plotter(fig, annote):
        axes = []
        pos = annote['argset']['POS']
        
        picklefiles = SubstitutionAnalysis.get_save_files(annote['argset'],
                                                          readonly=True)
        res = ps.load(picklefiles[annote['fname']])
        
        ax = fig.add_subplot(311)
        axes.append(ax)
        ax.set_title('Base feature / Start / Arrival distribution')
        bins = ax.hist(fv[pos], bins=30, color='r', alpha=0.5,
                       label='Base features')[1]
        ax.legend()
        xlim = ax.get_xlim()
        
        ax = fig.add_subplot(312)
        axes.append(ax)
        ax.hist(res[:, 0], bins=bins, color='b', alpha=0.5, label='Starts')
        ax.legend()
        ax.set_xlim(xlim)
        
        ax = fig.add_subplot(313)
        axes.append(ax)
        ax.hist(res[:, 1], bins=bins, color='g', alpha=0.5, label='Arrivals')
        ax.legend()
        ax.set_xlim(xlim)
        
        return axes
    
    af = an.AnnoteFinderPointPlot(pl.arange(l), r_avgs, annotes, formatter,
                                  side_plotter, ytol=0.5)
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
      * build_clids: build a dict associating cluster ids to the lists of the
                     coordinates of their appearance in 'details'
      * clmeans: compute the means of a list of values, grouped by cluster ids
      * destination_features: get the feature values that were jumped to,
                              coming from feature values in start_range
      * feature_range_ratio: compute the mean substitution ratio for starting
                             features with values in 'start_range', together
                             with IC-95% half-width
    
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
        
        self.clids = self.build_clids(details)
        
        # Compute ratios, correct them to represent the means
        # by clusters.
        
        self.ratios = data[:, 1] / data[:, 0]
        self.ratios_cl = self.clmeans(self.ratios, self.clids)
    
    def build_clids(self, details):
        """Build a dict associating cluster ids to the lists of the
        coordinates of their appearance in 'details'."""
        return list_to_dict([detail['mother'].cl_id for detail in details])
    
    def clmeans(self, values, clids):
        """Compute the means of a list of values, grouped by cluster ids."""
        means = []
        
        for idx in clids.itervalues():
            means.append(values[idx].mean())
        
        return array(means)
    
    def destination_features(self, start_range):
        """Get the feature values that were jumped to, coming from feature
        values in start_range."""
        idx = pl.where((start_range[0] <= self.data[:, 0])
                       * (self.data[:, 0] <= start_range[1]))[0]
        
        # Check we got something.
        
        if len(idx) == 0:
            return None
        
        return self.data[idx, 1]
    
    def feature_range_ratio(self, start_range):
        """Compute the mean substitution ratio for starting features with
        values in 'start_range', together with IC-95% half-width."""
        idx = pl.where((start_range[0] <= self.data[:, 0])
                       * (self.data[:, 0] <= start_range[1]))[0]
        
        # Check we got something.
        
        if len(idx) == 0:
            return None
        
        clids = self.build_clids([self.details[i] for i in idx])
        ratios = self.data[idx, 1] / self.data[idx, 0]
        ratios_cl = self.clmeans(ratios, clids)
        ic = (1.96 * ratios_cl.std() / pl.sqrt(len(ratios_cl) - 1))
        
        return ratios_cl.mean(), ic


def iter_argsets_results(args):
    """Iterate through all substitution analysis results corresponding to
    given args."""
    argsets = SubstitutionAnalysis.create_argsets(args)
    
    for argset in argsets:
        
        # Load the data.
        
        pickle_files = SubstitutionAnalysis.get_save_files(argset,
                                                           readonly=True)
        
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


def load_ratio_results(args):
    """Load all the results of substitution analysis corresponding to given
    args."""
    
    argsets = []
    results = dict([(fname, {'r_avgs': [], 'r_stds': [], 'r_lens': [],
                             'r_clids': [], 'r_ics': None})
                    for fname in st.memetracker_subst_fnames])
    
    for argset, res in iter_argsets_results(args):
        
        argsets.append(argset)
        
        for fname in st.memetracker_subst_fnames:
            results[fname]['r_avgs'].append(res[fname].ratios_cl.mean())
            results[fname]['r_stds'].append(res[fname].ratios_cl.std())
            results[fname]['r_lens'].append(res[fname].length)
            results[fname]['r_clids'].append(res[fname].clids)
    
    return argsets, results


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
