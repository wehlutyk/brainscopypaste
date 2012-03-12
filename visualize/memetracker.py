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
def view_timeline(timeline, legend_item='no id', mean_res=5):
    '''
    Plot a timeline.
    mean_res is the number of days used to compute an additional smoothed curve
    set mean_res to -1 to disable the additional smoothed curve
    '''
    
    # Do the histogram
    days_span = int(round(timeline_span(timeline).total_seconds() / 86400))
    freqs, bins = pl.histogram(timeline, days_span)
    x_secs = (bins[:-1] + bins[1:])//2
    
    # Convert the epoch-timestamps to dates
    x_dates = []
    for d in x_secs:
        x_dates.append(datetime.fromtimestamp(d))
    
    # Plot
    pl.plot_date(x_dates, freqs, xdate=True, fmt='-', label='*Quotes per day* ({})'.format(legend_item))
    
    # And show a smoothed curve if there's enough data, and if we weren't asked not to
    if mean_res != -1 and days_span > mean_res:
        x_secs_interp, freqs_interp = smooth_data(x_secs, freqs, mean_res)
        x_dates_interp = []
        for d in x_secs_interp:
            x_dates_interp.append(datetime.fromtimestamp(d))
        pl.plot_date(x_dates_interp, freqs_interp, xdate=True, fmt='-', label='{}-day moving average ({})'.format(mean_res, legend_item))
    
    # Show the legend
    pl.legend(loc='best')


def timeline_span(timeline):
    return datetime.fromtimestamp(timeline.max()) - datetime.fromtimestamp(timeline.min())


def smooth_data(x_secs, freqs, mean_res):
    start = int(pl.ceil(mean_res/2))
    end = len(x_secs)-start+1
    length = end - start
    x_secs_interp = x_secs[start:end]
    freqs_interp = pl.mean([freqs[i:length+i] for i in range(mean_res)], 0)
    return (x_secs_interp, freqs_interp)
