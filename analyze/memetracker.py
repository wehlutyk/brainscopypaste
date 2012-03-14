#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Tools to analyse data from the MemeTracker dataset
'''


# Imports
from __future__ import division
import datainterfaces.memetracker as d_mt
import numpy as np


# Module code
def frame_cluster_5day(cluster):
    '''
    Create a new cluster by cropping the one passed as an argument in a +/-48h time frame
    around the 24h with highest activity
    '''
    
    # How many days to keep, around the 24 hours with maximum activity
    span_before = 2 * 86400
    span_after = 2 * 86400
    
    cluster.build_timeline()
    max_24h = find_max_24h_frame(cluster.timeline)
    
    start = max_24h - span_before
    end = max_24h + 86400 + span_after
    
    return frame_cluster(cluster, start, end)


def frame_cluster(cl, start, end):
    framed_quotes = {}
    for qt in cl.quotes.values():
        qt.compute_attrs()
        if (start <= qt.start <= end) or (qt.start <= start <= qt.end):
            framed_quotes[qt.id] = frame_quote(qt, start, end)
    
    n_quotes = len(framed_quotes)
    tot_freq = sum([qt.tot_freq for qt in framed_quotes.values()])
    framed_cluster = d_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq, root=cl.root, cl_id=cl.id)
    framed_cluster.quotes = framed_quotes
    
    return framed_cluster


def frame_quote(qt, start, end):
    '''
    Create a new quote from the one passed as an argument, but framed in the time-window [start, end]
    '''
    
    framed_times = frame_timeline(qt, start, end)
    n_urls = len(set(framed_times))
    tot_freq = len(framed_times)
    framed_qt = d_mt.Quote(n_urls=n_urls, tot_freq=tot_freq, string=qt.string, qt_id=qt.id)
    framed_qt.url_times = framed_times
    framed_qt.current_idx = tot_freq
    framed_qt.compute_attrs()
    return framed_qt


def frame_timeline(tm, start, end):
    return tm.url_times[np.where((start <= tm.url_times) * (tm.url_times <= end))].copy()


def find_max_24h_frame(timeline):
    '''
    Find the 24h window (+/-some precision threshold) with the most activity
    '''
    
    prec = 30*60    # Half-hour precision
    n_windows = int(np.ceil(2*86400/prec))
    
    if not timeline.attrs_computed:
        timeline.compute_attrs()
    
    base_time = timeline.max_ipd_x_secs - 86400
    start_times = np.arange(n_windows)*prec + base_time
    
    ipd_all = np.zeros(n_windows)
    for i, st in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1, (st, st+86400))[0][0]
    
    return start_times[np.argmax(ipd_all)]


#def get_timebags(cluster, n_bags):
#    '''
#    Return n_bags bags of quotes computed from the cluster (time bags)
#    '''
#    pass
#
#
#class TimeBag(object):
#    def __init__(self, cluster, start, end):
#        pass