#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Methods to visualize data from the MemeTracker dataset
'''


# Imports
from __future__ import division
from datetime import datetime
import pylab as pl


# Module code
def plot_timeline(timeline, label='raw timeline, no info', smooth_res=5, legend_size=10.0):
    '''
    Plot a timeline.
    smooth_res is the number of days used to compute an additional smoothed curve
    set smooth_res to -1 to disable the additional smoothed curve
    '''
    
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
    pl.legend(loc='best', prop={'size': legend_size})


def smooth_data(x_secs, ipd, smooth_res):
    start = int(pl.ceil(smooth_res/2))
    end = len(x_secs)-start+1
    length = end - start
    x_secs_smooth = x_secs[start:end]
    ipd_smooth = pl.mean([ipd[i:length+i] for i in range(smooth_res)], 0)
    return (x_secs_smooth, ipd_smooth)
