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
def view_timeline(timeline, mean_res=5):
    # Do the histogram
    days_span = int(round(timeline_span(timeline).total_seconds() / 86400))
    freqs, bins = pl.histogram(timeline, days_span)
    x_secs = (bins[:-1] + bins[1:])//2
    
    # Smooth the curve
    x_secs_interp, freqs_interp = smooth_data(x_secs, freqs, mean_res)
    
    # Now convert the epoch-timestamps to dates
    x_dates = []
    for d in x_secs:
        x_dates.append(datetime.fromtimestamp(d))
    x_dates_interp = []
    for d in x_secs_interp:
        x_dates_interp.append(datetime.fromtimestamp(d))
    
    pl.figure()
    pl.plot_date(x_dates, freqs, xdate=True, fmt='-')
    pl.plot_date(x_dates_interp, freqs_interp, xdate=True, fmt='-')
    pl.legend(['*Quotes per day*', '{}-day moving average'.format(mean_res)], loc='best')


def timeline_span(timeline):
    return datetime.fromtimestamp(timeline.max()) - datetime.fromtimestamp(timeline.min())


def smooth_data(x_secs, freqs, mean_res):
    start = int(pl.ceil(mean_res/2))
    end = len(x_secs)-start+1
    length = end - start
    x_secs_interp = x_secs[start:end]
    freqs_interp = pl.mean([freqs[i:length+i] for i in range(mean_res)], 0)
    return (x_secs_interp, freqs_interp)
