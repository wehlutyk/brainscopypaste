#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Tools to analyse data from the MemeTracker dataset
'''


# Imports
from __future__ import division
from nltk import word_tokenize
import datastructure.memetracker as ds_mt
import numpy as np


# Module code
def frame_cluster_around_peak(cl, span_before=2*86400, span_after=2*86400):
    '''
    Create a new cluster by cropping the one passed as an argument in a +/-48h time frame
    around the 24h with highest activity
    '''
    
    cl.build_timeline()
    max_24h = find_max_24h_frame(cl.timeline)
    
    start = max_24h - span_before
    end = max_24h + 86400 + span_after
    
    return frame_cluster(cl, start, end)


def frame_cluster(cl, start, end):
    framed_quotes = {}
    for qt in cl.quotes.values():
        qt.compute_attrs()
        if (start <= qt.start <= end) or (qt.start <= start <= qt.end):
            framed_quote = frame_quote(qt, start, end)
            if framed_quote != None:
                framed_quotes[qt.id] = framed_quote
    
    n_quotes = len(framed_quotes)
    tot_freq = sum([qt.tot_freq for qt in framed_quotes.values()])
    framed_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq, root=cl.root, cl_id=cl.id)
    framed_cluster.quotes = framed_quotes
    
    return framed_cluster


def frame_quote(qt, start, end):
    '''
    Create a new quote from the one passed as an argument, but framed in the time-window [start, end]
    '''
    
    framed_times = frame_timeline(qt, start, end)
    if len(framed_times) == 0:
        return None
    n_urls = len(set(framed_times))
    tot_freq = len(framed_times)
    framed_qt = ds_mt.Quote(n_urls=n_urls, tot_freq=tot_freq, string=qt.string, qt_id=qt.id)
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


def get_timebags(cluster, n_bags):
    '''
    Return n_bags bags of quotes computed from the cluster (time bags)
    '''
    
    cluster.build_timeline()
    step = int(round(cluster.timeline.span.total_seconds() / n_bags))
    cl_start = cluster.timeline.start
    
    timebags = []
    for i in xrange(n_bags):
        timebags.append(ds_mt.TimeBag(cluster, cl_start + i*step, cl_start + (i+1)*step))
    
    return timebags


def build_n_quotes_to_clusterids(clusters):
    inv_cl_lengths = {}
    for cl in clusters.values():
        if inv_cl_lengths.has_key(cl.n_quotes):
            inv_cl_lengths[cl.n_quotes].append(cl.id)
        else:
            inv_cl_lengths[cl.n_quotes] = [cl.id]
    return inv_cl_lengths


def build_quotelengths_to_quoteids(clusters):
    inv_qt_lengths = {}
    for cl in clusters.values():
        for qt in cl.quotes.values():
            n_words = len(word_tokenize(qt.string.lower()))
            if inv_qt_lengths.has_key(n_words):
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1