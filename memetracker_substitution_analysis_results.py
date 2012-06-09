#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot results from the memetracker_substitution_analysis_all script."""


from __future__ import division

from warnings import warn

from numpy import array
import pylab as pl
import matplotlib.cm as cm

import datainterface.picklesaver as ps
from analyze.memetracker import SubstitutionAnalysis
import visualize.annotations as an
import settings as st


def average_ntb_ratios(xpos, l_clids, l_scores):
    """Concatenate score data sets from different parameter sets into a
    single set of ratios averaged and weighted over the pooled clusters."""
    cl_avgvalues = {}
    
    for x in xpos:
        
        for clid, coords in l_clids[x].iteritems():
            
            avg = (l_scores[x][coords, 1] / l_scores[x][coords, 0]).mean()
            
            if cl_avgvalues.has_key(clid):
                cl_avgvalues[clid][0].append(avg)
                cl_avgvalues[clid][1].append(len(coords))
            else:
                cl_avgvalues[clid] = ([avg], [len(coords)])
    
    means = [pl.average(avgs, weights=weights)
             for avgs, weights in cl_avgvalues.itervalues()]
    
    return array(means)


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


def plot_dataseries(h0, r_avgs, r_ics, scores_all, r_clids, annotes,
                      title, POS_series, ff_series, ntb_series, parameters_d):
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
        pl.plot(xpos, pl.ones(len(xpos)) * h0[pos], 'k--', linewidth=2,
                label=lbl)
        pl.fill_between([min(xpos) - 0.5, max(xpos) + 0.5], ytop2, ybot,
                        color=col_POS[pos], edgecolor=(0, 0, 0, 0))
        pl.text((min(xpos) + max(xpos)) / 2, ytop1, pos,
                bbox=dict(facecolor='white', edgecolor='white', alpha=0.8),
                ha='center', va='center')
    
    setlabel = True
    for ntb, xntb in ntb_series:
        
#        ntb_r_avgs = average_ntb_ratios(xntb, r_clids, scores_all)
#        ntb_r_avgs_mean = ntb_r_avgs.mean()
#        ntb_r_avgs_ic = (1.96 * ntb_r_avgs.std() /
#                         pl.sqrt(len(ntb_r_avgs) - 1))
        
        lbl = 'averages' if setlabel else None
        pl.plot(xntb, r_avgs[xntb], 'b-', linewidth=2, label=lbl)
        lbl = 'avgs +/- IC-95%' if setlabel else None
        pl.plot(xntb, r_avgs[xntb] - r_ics[xntb], 'c-', linewidth=1,
                label=lbl)
#        lbl = 'avgs_ntb' if setlabel else None
#        pl.plot(xntb, pl.ones(len(xntb)) * ntb_r_avgs_mean, 'r-', lw=2,
#                label=lbl, zorder=100)
#        lbl = 'avgs_ntb +/- IC-95%' if setlabel else None
#        pl.plot(xntb,
#                pl.ones(len(xntb)) * (ntb_r_avgs_mean - ntb_r_avgs_ic),
#                'm-', label=lbl, zorder=100)
        setlabel = False
        
#        pl.plot(xntb,
#                pl.ones(len(xntb)) * (ntb_r_avgs_mean + ntb_r_avgs_ic),
#                'm-', zorder=100)
        pl.plot(xntb, r_avgs[xntb] + r_ics[xntb], 'c-', linewidth=1)
        pl.plot(xntb, r_avgs[xntb], 'bo', linewidth=2)
        pl.plot(xntb, r_avgs[xntb] - r_ics[xntb], 'c.', linewidth=1)
        pl.plot(xntb, r_avgs[xntb] + r_ics[xntb], 'c.', linewidth=1)
    
    for ff, xff in ff_series:
        
        pl.fill([xff[0] - 0.5, xff[0] - 0.5, xff[-1] + 0.5, xff[-1] + 0.5],
                [ytop4, ytop2, ytop2, ytop4], color=col_ff[ff],
                edgecolor = (0, 0, 0, 0), hatch=hatch_ff[ff])
        pl.text((min(xff) + max(xff)) / 2, ytop3, ff,
                bbox=dict(facecolor='white', edgecolor='white', alpha=0.8),
                ha='center', va='center')
    
    for ntb, xntb in ntb_series:
        
        pl.plot([xntb[0] - 0.5, xntb[0] - 0.5], [ybot, ytop0],
                color=(0.5, 0.5, 0.5, 0.3))
        pl.plot([xntb[-1] + 0.5, xntb[-1] + 0.5], [ybot, ytop0],
                color=(0.5, 0.5, 0.5, 0.3))
        pl.text((min(xntb) + max(xntb)) / 2, ytop0, '{}'.format(ntb),
                bbox=dict(facecolor='white', edgecolor='white', alpha=0.8),
                ha='center', va='center')
    
    ax.set_xlim(xleft, xright)
    ax.set_ylim(ybot, ytop4)
    pl.legend(loc='best', prop=dict(size='small'))
    pl.title(title)
    
    ax.set_xticks(range(l))
    labels = ax.set_xticklabels(['{}'.format(p['n_timebags'])
                                 for p in parameters_d])
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


class DictNS(object):
    
    """A dummy class to turn a dict into a namespace."""
    
    def __init__(self, d):
        self.__dict__.update(d)


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
    af_wn_sra, af2_wn_sra = plot_dataseries(wn_PR_h0, wn_PR_scores_r_avgs,
                                            wn_PR_scores_r_ics,
                                            wn_PR_scores_a,
                                            wn_PR_scores_r_clids,
                                            wn_PR_annotes,
                                            title_wn_sra,
                                            POS_series, ff_series, ntb_series,
                                            parameters_d)
    title_wn_dra = \
        'WN Degrees ratio [substitutions={}, substrings={}]'.format(
                                                                substitutions,
                                                                substrings)
    af_wn_dra, af2_wn_dra = plot_dataseries(wn_DEG_h0, wn_degrees_r_avgs,
                                            wn_degrees_r_ics,
                                            wn_degrees_a,
                                            wn_degrees_r_clids,
                                            wn_DEG_annotes,
                                            title_wn_dra,
                                            POS_series, ff_series, ntb_series,
                                            parameters_d)
    title_fa_sra = \
        'FA PR scores ratio [substitutions={}, substrings={}]'.format(
                                                                substitutions,
                                                                substrings)
    af_fa_sra, af2_fa_sra = plot_dataseries(fa_PR_h0, fa_PR_scores_r_avgs,
                                            fa_PR_scores_r_ics,
                                            fa_PR_scores_a,
                                            fa_PR_scores_r_clids,
                                            fa_PR_annotes,
                                            title_fa_sra,
                                            POS_series, ff_series, ntb_series,
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
