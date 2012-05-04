#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Visualize data from the MemeTracker dataset

Methods:
  * plot_timeline: plot the evolution of a Timeline, with an optional legend
                   and an optional moving average
  * smooth_data: compute a moving average of a histogram (used in
                 'plot_timeline')
  * dt_toordinal: convert a datetime object to an ordinal, as used by
                  Matplotlib
  * bar_timeline: plot the bar-chart of a Timeline
  * bar_cluster: plot the stacked bar-chart of Quotes in a Cluster, with added
                 annotations
  * bar_cluster_norm: plot the normalized stacked bar-chart of Quotes in a
                      Cluster, with added text-less annotations

Classes:
  * ordTimeDelta: subclass of timedelta that defines the 'toordinal' method,
                  for use in Matplotlib

"""


from __future__ import division

from datetime import datetime, timedelta
from operator import attrgetter

import numpy as np
import pylab as pl
import matplotlib.dates as md
import matplotlib.cm as cm

import visualize.annotations as v_an


def plot_timeline(timeline, label='raw timeline, no info', smooth_res=5,
                    legend_on=True, legend_size=10.0):
    """Plot the evolution of a Timeline, with an optional legend and an
    optional moving average.
    
    Arguments:
      * timeline: the Timeline to plot
    
    Optional arguments:
      * label: a legend label; defaults to 'raw timeline, no info'
      * smooth_res: the width, in days, of the moving average; if -1 is given,
                    no moving average is plotted. Defaults to 5 days.
      * legend_on: boolean specifying if the legend is to be shown or not.
                   Defaults to True.
      * legend_size: float specifying the font size of the legend. Defaults
                     to 10.0.
    
    """
    
    timeline.compute_attrs()
    
    # Convert the epoch-timestamps to dates.
    
    x_dates = []
    
    for d in timeline.ipd_x_secs:
        x_dates.append(datetime.fromtimestamp(d))
    
    # 'ipd' stands for Instances per Day.
    
    pl.plot_date(x_dates, timeline.ipd, xdate=True, fmt='-',
                 label='{} (ipd)'.format(label))
    
    # Show a smoothed curve if there's enough data, and if we weren't asked
    # not to.
    
    if smooth_res != -1 and timeline.span_days > smooth_res:
        
        x_secs_smooth, ipd_smooth = smooth_data(timeline.ipd_x_secs,
                                                timeline.ipd, smooth_res)
        x_dates_smooth = []
        
        for d in x_secs_smooth:
            x_dates_smooth.append(datetime.fromtimestamp(d))
            
        pl.plot_date(x_dates_smooth, ipd_smooth, xdate=True, fmt='-',
                     label='{} ({}-day moving average)'.format(label,
                                                               smooth_res))
    
    if legend_on:
        pl.legend(loc='best', prop={'size': legend_size})


def smooth_data(x_secs, ipd, smooth_res):
    """Compute a moving average of a histogram (used in plot_timeline).
    
    Arguments:
      * x_secs: the x values of the histogram (i.e. the middles of the bins)
      * ipd: the histogram values to be smoothed (ipd stands for instances
             per day)
      * smooth_res: the width, in days, of the moving average to be computed
    
    Returns: a tuple (x_secs_smooth, ipd_smooth) containing the x and y values
             for the computed moving average.
    
    """
    
    start = int(pl.ceil(smooth_res / 2))
    end = len(x_secs) - start + 1
    length = end - start
    
    x_secs_smooth = x_secs[start:end]
    ipd_smooth = pl.mean([ipd[i:length + i] for i in range(smooth_res)], 0)
    
    return (x_secs_smooth, ipd_smooth)


class ordTimeDelta(timedelta):
    
    """Subclass of timedelta that defines the 'toordinal' method, for use in
    Matplotlib.
    
    Methods:
      * toordinal: return the ordinal representation of the TimeDelta object
    
    """
    
    def toordinal(self):
        """Return the ordinal representation of the TimeDelta object."""
        return self.days + self.seconds / 86400


def dt_toordinal(dt):
    """Convert a datetime object to an ordinal, as used by Matplotlib."""
    return (dt.toordinal() + dt.hour / 24 + dt.minute / 1440 +
            dt.second / 86400)


def bar_timeline(timeline, bins=50):
    """Plot the bar-chart of a Timeline.
    
    Arguments:
      * timeline: the Timeline object to plot
    
    Optional arguments:
      * bins: same argument as the pylab.histogram function (either a integer
              or an array specifying the bin limits). Defaults to 50.
    
    Returns: the bin limits as returned by pylab.histogram.
    
    """
    
    fig = pl.gcf()
    ax = pl.gca()
    
    # Get the histogram data, and convert the bins to datetime formats.
    
    heights, bins = pl.histogram(timeline.url_times, bins=bins)
    widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                i in range(len(bins) - 1)]
    bins_d = [datetime.utcfromtimestamp(binlim) for binlim in bins]
    
    # Plot the bars.
    
    ax.bar(bins_d[:-1], heights, widths_d)
    ax.set_xlim(min(bins_d), max(bins_d))
    ax.set_ylim(-0.1 * max(heights), 1.1 * max(heights))
    
    # Format the date on the x axis and the coordinate box.
    
    loc = md.AutoDateLocator()
    formatter = md.AutoDateFormatter(loc)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
    fig.autofmt_xdate()
    
    return bins


def bar_cluster(cl, bins=50):
    """Plot the stacked bar-chart of Quotes in a Cluster, with added
    annotations.
    
    Arguments:
      * cl: the cluster to plot
    
    Optional arguments:
      * bins: same argument as the pylab.histogram function (either a integer
              or an array specifying the bin limits). Defaults to 50.
    
    Returns: a tuple consisting of the bins returned by pylab.histogram on the
             Cluster's full Timeline, and of the AnnoteFinderBar object linked
             to the plot.
    
    """
    
    fig = pl.gcf()
    ax = pl.gca()
    
    # Get the bins, to be given as common argument for all Quotes, later on.
    
    cl.build_timeline()
    cl_heights, bins = pl.histogram(cl.timeline.url_times, bins=bins)
    
    nbins = len(bins) - 1
    widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                i in range(nbins)]
    binlims_d = [datetime.utcfromtimestamp(binlim) for binlim in bins]
    
    # For future use in plotting and with the annotations.
    
    bottoms = np.zeros(nbins)
    l_bottoms = []
    l_heights = []
    l_quotes = sorted(cl.quotes.itervalues(), key=attrgetter('tot_freq'),
                      reverse=True)
    
    # Do the Quote plotting.
    
    for i, qt in enumerate(l_quotes):
        
        heights = pl.histogram(qt.url_times, bins=bins)[0]
        ax.bar(left=binlims_d[:-1], height=heights, width=widths_d,
               bottom=bottoms, color=cm.YlOrBr(i / cl.n_quotes))
        l_bottoms.append(bottoms.copy())
        l_heights.append(heights.copy())
        bottoms += heights
    
    ax.set_xlim(min(binlims_d), max(binlims_d))
    ax.set_ylim(-0.1 * max(cl_heights), 1.1 * max(cl_heights))
    
    # Format the date on the x axis and the coordinate box.
    
    loc = md.AutoDateLocator()
    formatter = md.AutoDateFormatter(loc)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
    fig.autofmt_xdate()
    
    # Create and link the annotations.
    
    af = v_an.AnnoteFinderBar(l_heights,
                              [[dt_toordinal(binlim)
                                for binlim in binlims_d]] * cl.n_quotes,
                              l_bottoms, l_quotes)
    pl.connect('button_press_event', af)
    
    return (bins, af)


def bar_cluster_norm(cl, bins=50):
    """Plot the normalized stacked bar-chart of Quotes in a Cluster, with
    added text-less annotations.
    
    Arguments:
      * cl: the cluster to plot
    
    Optional arguments:
      * bins: same argument as the pylab.histogram function (either a integer
              or an array specifying the bin limits). Defaults to 50.
    
    Returns: a tuple consisting of the bins returned by pylab.histogram on the
             Cluster's full Timeline, and of the AnnoteFinderBar object linked
             to the plot. The annotations linked to the plot display no text,
             and will only highlight the bars corresponding to the selected
             Quote. This is meant to be linked to the AnnoteFinderBar object
             returned by bar_cluster, to have those two subplots linked
             together in the same figure.
    
    """
    
    fig = pl.gcf()
    ax = pl.gca()
    
    # Get the bins, to be given as common argument for all Quotes, later on.
    
    cl.build_timeline()
    cl_heights, bins = pl.histogram(cl.timeline.url_times, bins=bins)
    
    nbins = len(bins) - 1
    widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                i in range(nbins)]
    binlims_d = [datetime.utcfromtimestamp(binlim) for binlim in bins]
    
    # For future use in plotting, normalizing, and annotating.
    
    bottoms = np.zeros(nbins)
    l_bottoms = []
    heights_qt = np.zeros((nbins, cl.n_quotes))
    l_quotes = sorted(cl.quotes.itervalues(), key=attrgetter('tot_freq'),
                      reverse=True)
    
    # Get the histogram data.
    
    for i, qt in enumerate(l_quotes):
        heights_qt[:, i] = pl.histogram(qt.url_times, bins=bins)[0]
    
    # Normalize all the heights to one.
    
    for j in range(nbins):
        
        if cl_heights[j] != 0:
            heights_qt[j, :] = heights_qt[j, :] / cl_heights[j]
    
    # Plot the normalized histograms.
    
    for i in range(cl.n_quotes):
        
        ax.bar(left=binlims_d[:-1], height=heights_qt[:, i], width=widths_d,
               bottom=bottoms, color=cm.YlOrBr(i / cl.n_quotes))
        l_bottoms.append(bottoms.copy())
        bottoms += heights_qt[:, i]
    
    ax.set_xlim(min(binlims_d), max(binlims_d))
    ax.set_ylim(-0.1, 1.1)
    
    # Format the date on the x axis and the coordinate box.
    
    loc = md.AutoDateLocator()
    formatter = md.AutoDateFormatter(loc)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
    fig.autofmt_xdate()
    
    # Create and link the annotations.
    
    af = v_an.AnnoteFinderBar(heights_qt.transpose(),
                              [[dt_toordinal(binlim)
                                for binlim in binlims_d]] * cl.n_quotes,
                              l_bottoms, l_quotes, drawtext=False)
    pl.connect('button_press_event', af)
    
    return (bins, af)
