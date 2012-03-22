#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Visualize data from the MemeTracker dataset

Methods:
  * plot_timeline: plot the evolution of a Timeline, with an optional legend and an optional moving average
  * smooth_data: compute a moving average of a histogram (used in plot_timeline)

"""


# Imports
from __future__ import division
from datetime import datetime
import pylab as pl


# Module code
def plot_timeline(timeline, label='raw timeline, no info', smooth_res=5, legend_on=True, legend_size=10.0):
    """Plot the evolution of a Timeline, with an optional legend and an optional moving average.
    
    Arguments:
      * timeline: the Timeline to plot
    
    Optional arguments:
      * label: a legend label; defaults to 'raw timeline, no info'
      * smooth_res: the width, in days, of the moving average; if -1 is given, no moving average is plotted;
                    defaults to 5 days
      * legend_on: boolean specifying if the legend is to be shown or not; defaults to True
      * legend_size: float specifying the font size of the legen; defaults to 10.0
    
    """
    
    if not timeline.attrs_computed:
        timeline.compute_attrs()
    
    # Convert the epoch-timestamps to dates
    x_dates = []
    for d in timeline.ipd_x_secs:
        x_dates.append(datetime.fromtimestamp(d))
    
    # Plot. 'ipd' stands for Instances per Day
    pl.plot_date(x_dates, timeline.ipd, xdate=True, fmt='-', label='{} (ipd)'.format(label))
    
    # And show a smoothed curve if there's enough data, and if we weren't asked not to
    if smooth_res != -1 and timeline.span_days > smooth_res:
        x_secs_smooth, ipd_smooth = smooth_data(timeline.ipd_x_secs, timeline.ipd, smooth_res)
        x_dates_smooth = []
        for d in x_secs_smooth:
            x_dates_smooth.append(datetime.fromtimestamp(d))
        pl.plot_date(x_dates_smooth, ipd_smooth, xdate=True, fmt='-', label='{} ({}-day moving average)'.format(label, smooth_res))
    
    # Show the legend
    if legend_on:
        pl.legend(loc='best', prop={'size': legend_size})


def smooth_data(x_secs, ipd, smooth_res):
    """Compute a moving average of a histogram (used in plot_timeline).
    
    Arguments:
      * x_secs: the x values of the histogram (i.e. the middles of the bins)
      * ipd: the histogram values to be smoothed (ipd stands for instances per day)
      * smooth_res: the width, in days, of the moving average to be computed
    
    Returns: a tuple (x_secs_smooth, ipd_smooth) containing the x and y values for the computed moving average.
    
    """
    
    start = int(pl.ceil(smooth_res/2))
    end = len(x_secs)-start+1
    length = end - start
    x_secs_smooth = x_secs[start:end]
    ipd_smooth = pl.mean([ipd[i:length+i] for i in range(smooth_res)], 0)
    return (x_secs_smooth, ipd_smooth)
