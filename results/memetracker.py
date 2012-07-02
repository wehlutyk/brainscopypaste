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
from matplotlib.colors import Normalize

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


def plot_substseries(h0, r_h0s, fv, fd, r_avgs, r_ics, r_clids, annotes,
                       title, POS_series, ff_series, argsets):
    """Plot a dataseries resulting from the substitution analysis."""
    cmap = cm.jet
    n_POSs = len(st.memetracker_subst_POSs)
    col_POS = dict([(pos, cmap(i / n_POSs, alpha=0.15))
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
        
        lbl = 'H0 feature' if setlabel else None
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
        
        # The h0s w/ respect to observed distributions
        
        lbl = 'H0 distrib' if setlabel else None
        pl.plot([i - 0.4, i + 0.4], [r_h0s[i], r_h0s[i]], 'c--',
                linewidth=2, label=lbl)
        
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
        details = ps.load(picklefiles[annote['fname_d']])
        fname_root = annote['fname'][:2]
        suscept_data = ps.load(picklefiles[fname_root + '_suscept_data'])
        suscept_dict = compute_susc(suscept_data, fname_root)
        
        # The Base features / Starts / Arrivals
        
        ax = fig.add_subplot(321)
        axes.append(ax)
        ax.set_title('Base feature / Start / Arrival distribution')
        bins = ax.hist(fv[pos], bins=20, color='r', alpha=0.5,
                       label='Base features', log=True)[1]
        ax.legend()
        xlim = ax.get_xlim()
        
        ax = fig.add_subplot(323)
        axes.append(ax)
        ax.hist(res[:, 0], bins=bins, color='b', alpha=0.5, label='Starts',
                log=True)
        ax.legend()
        ax.set_xlim(xlim)
        
        ax = fig.add_subplot(325)
        axes.append(ax)
        ax.hist(res[:, 1], bins=bins, color='g', alpha=0.5, label='Arrivals',
                log=True)
        ax.legend()
        ax.set_xlim(xlim)
        
        # The mean ratio for different start features
        
        nbins = 20
        f = ArgsetResults(res, details)
        rng = (pl.amin(f.data), pl.amax(f.data))
        bins = pl.linspace(rng[0], rng[1], nbins + 1)
        x = (bins[1:] + bins[:-1]) / 2
        
        fv_idxs = [pl.where((bins[j] <= fv[pos]) * (fv[pos] <= bins[j + 1]))
                   for j in range(nbins)]
        h0 = fv[pos].mean() * array([(1 / fv[pos][fv_idxs[j]]).mean()
                                     for j in range(nbins)])
        
        ratios_h0s_ics = [f.feature_range_ratio([bins[j], bins[j + 1]])
                          for j in range(nbins)]
        ratios = []
        ratios_p_ics = []
        ratios_m_ics = []
        h0s = []
        
        for ric in ratios_h0s_ics:
            
            if ric != None:
                
                ratios.append(ric[0])
                ratios_p_ics.append(ric[0] + ric[2])
                ratios_m_ics.append(ric[0] - ric[2])
                h0s.append(ric[1])
            
            else:
                
                ratios.append(None)
                ratios_p_ics.append(None)
                ratios_m_ics.append(None)
                h0s.append(None)
        
        ax = fig.add_subplot(322)
        axes.append(ax)
        ax.set_title(u'Ratio moyen pour des départs différents')
        ax.plot(x, ratios, 'b-', label='Measured')
        ax.plot(x, ratios_p_ics, 'm-', label='IC-95%')
        ax.plot(x, ratios_m_ics, 'm-')
        ax.plot(x, h0s, 'c-', label='H0 distrib')
        ax.plot(x, h0, 'k-', label='H0 feature')
        ax.legend()
        
        # Mots de départ / arrviée font quelle proportion du pool
        
        nbins = 20
        
        ax = fig.add_subplot(324)
        axes.append(ax)
        cmap = cm.YlGnBu
        
        ax.set_title(u'Susceptibilité des mots de départ')
        bins, patches = ax.hist(fv[pos], bins=nbins, log=True,
                                label='Start words')[1:]
        
        lem_list = [d['lem1'] for d in f.details]
        suscepts = pl.array([get_feature_suscept(fd[pos], lem_list,
                                                 suscept_dict,
                                                 [bins[i], bins[i + 1]])
                             for i in range(nbins)])
        susceptsn = ((suscepts - suscepts.min()) /
                     (suscepts.max() - suscepts.min()))
        
        for i in range(nbins):
            patches[i].set_color(cmap(susceptsn[i]))
        
        sm = cm.ScalarMappable(Normalize(suscepts.min(), suscepts.max()), cmap)
        sm.set_array(suscepts)
        cb = fig.colorbar(sm, ax=ax)
        axes.append(cb.ax)
        ax.legend()
        
        ax = fig.add_subplot(326)
        axes.append(ax)
        
        ax.set_title(u'Proportion des mots de départ dans le pool de features')
        bins, patches = ax.hist(fv[pos], bins=nbins, log=True,
                                label='Start words')[1:]
        
        lem_list = [d['lem1'] for d in f.details]
        props = pl.array([get_feature_prop(lem_list, fd[pos],
                                           [bins[i], bins[i + 1]])
                          for i in range(nbins)])
        propsn = (props - props.min()) / (props.max() - props.min())
        for i in range(nbins):
            patches[i].set_color(cmap(propsn[i]))
        
        sm = cm.ScalarMappable(Normalize(props.min(), props.max()), cmap)
        sm.set_array(props)
        cb = fig.colorbar(sm, ax=ax)
        axes.append(cb.ax)
        ax.legend()
        
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
        self.h0_cl = (self.clmeans(data[:, 1], self.clids).mean()
                      * (1 / self.clmeans(data[:, 0], self.clids)).mean())
    
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
        data_rng = self.data[idx, :]
        ratios = data_rng[:, 1] / data_rng[:, 0]
        ratios_cl = self.clmeans(ratios, clids)
        h0_cl = (self.clmeans(data_rng[:, 1], clids).mean()
                 * (1 / self.clmeans(data_rng[:, 0], clids)).mean())
        ic = (1.96 * ratios_cl.std() / pl.sqrt(len(ratios_cl) - 1))
        
        return ratios_cl.mean(), h0_cl, ic


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
        wn_suscept_data = ps.load(pickle_files['wn_suscept_data'])
        fa_suscept_data = ps.load(pickle_files['fa_suscept_data'])
        
        
        if (wn_PR_scores == None or wn_degrees == None or
            fa_PR_scores.length == None):
            warn('{}: empty data'.format(argset))
            continue
        
        yield argset, {'wn_PR_scores': wn_PR_scores,
                       'wn_degrees': wn_degrees,
                       'fa_PR_scores': fa_PR_scores,
                       'wn_suscept_data': wn_suscept_data,
                       'fa_suscept_data': fa_suscept_data}


def compute_susc(suscept_data, fname_root):
    """Compute the susceptitbility of each word according to 'suscept_data'."""
    poss = suscept_data[fname_root + '_possibilities']
    real = suscept_data[fname_root + '_realised']
    susc = {}
    
    for word, p in poss.iteritems():
        
        if real.has_key(word):
            susc[word] = real[word] / p
        else:
            susc[word] = 0.0
    
    return susc


def load_ratio_results(args):
    """Load all the results of substitution analysis corresponding to given
    args."""
    
    argsets = []
    results = dict([(fname, {'r_avgs': [], 'r_stds': [], 'r_lens': [],
                             'r_clids': [], 'r_ics': None, 'r_h0s': []})
                    for fname in st.memetracker_subst_fnames])
    
    for argset, res in iter_argsets_results(args):
        
        argsets.append(argset)
        
        for fname in st.memetracker_subst_fnames:
            results[fname]['r_avgs'].append(res[fname].ratios_cl.mean())
            results[fname]['r_stds'].append(res[fname].ratios_cl.std())
            results[fname]['r_lens'].append(res[fname].length)
            results[fname]['r_clids'].append(res[fname].clids)
            results[fname]['r_h0s'].append(res[fname].h0_cl)
    
    return argsets, results


def features_to_values(features):
    values = {}
    
    for fname in st.memetracker_subst_fnames:
        
        values[fname] = {}
        
        for pos in st.memetracker_subst_POSs:
            values[fname][pos] = array(features[fname][pos].values())
    
    return values


def load_features():
    wn_PR_scores = {}
    wn_degrees = {}
    
    for pos in st.memetracker_subst_POSs:
        
        wn_PR_scores[pos] = ps.load(st.wordnet_PR_scores_pickle.format(pos))
        wn_degrees[pos] = ps.load(st.wordnet_degrees_pickle.format(pos))
    
    fa_PR_scores0 = ps.load(st.freeassociation_norms_PR_scores_pickle)
    fa_PR_scores = dict([(pos, fa_PR_scores0)
                         for pos in st.memetracker_subst_POSs])
    
    return {'wn_PR_scores': wn_PR_scores, 'wn_degrees': wn_degrees,
            'fa_PR_scores': fa_PR_scores}


def get_feature_prop(lem_list, fd, rng):
    flems_rng = set([lem for lem, v in fd.iteritems()
                     if rng[0] <= v and v <= rng[1]])
    if len(flems_rng) == 0:
        return 0
    intersect = flems_rng.intersection(lem_list)
    return len(intersect) / len(flems_rng)


def get_feature_suscept(fd, start_lems, suscept_dict, rng):
    start_lems_rng = set([lem for lem in start_lems
                          if rng[0] <= fd[lem] and fd[lem] <= rng[1]])
    if len(start_lems_rng) == 0:
        return 0
    lem_suscepts = pl.array([suscept_dict[lem] for lem in start_lems_rng])
    return lem_suscepts.mean()
