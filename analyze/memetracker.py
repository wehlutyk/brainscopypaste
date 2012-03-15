#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analysis methods for the MemeTracker dataset.

Methods:
  * frame_cluster_around_peak: cut off quote occurrences in a Cluster around the 24h
                               window with maximum activity
  * frame_cluster: cut off quote occurrences in a Cluster at the specified boundaries
  * frame_quote: cut off quote occurrences in a Quote at the specified boundaries
  * frame_timeline: cut off quote occurrences in a Timeline at the specified boundaries
  * find_max_24h_window: find the 24h window of maximum activity in a Timeline
  * build_timebags: build a number of TimeBags from a Cluster
  * build_n_quotes_to_clusterids: build a dict associating number of Quotes to
                                  Cluster ids having that number of quotes
  * build_quoteslengths_to_quoteids: build a dict associating Quote string lengths to
                                     the number of Quotes having that string length
"""


# Imports
from __future__ import division
import numpy as np
from nltk import word_tokenize
import datastructure.memetracker as ds_mt


# Module code
def frame_cluster_around_peak(cl, span_before=2*86400, span_after=2*86400):
    """Cut off quote occurrences in a Cluster around the 24h window with maximum activity.
    
    Arguments:
      * cl: the Cluster to work on
      * span_before: time span (in seconds) to include before the beginning of the max 24h window
      * span_after: time span (in seconds) to include after the end of the max 24h window
    
    Returns: a new framed Cluster.
    """
    
    cl.build_timeline()
    max_24h = find_max_24h_window(cl.timeline)
    
    start = max_24h - span_before
    end = max_24h + 86400 + span_after
    
    return frame_cluster(cl, start, end)


def frame_cluster(cl, start, end):
    """Cut off quote occurrences in a Cluster at the specified boundaries.
    
    Arguments:
      * cl: the Cluster to work on
      * start: time (in seconds from epoch) of the beginning of the target time window
      * end: time (in seconds from epoch) of the end of the target time window
    
    Returns: a new framed Cluster.
    """
    
    # Recreate each Quote, framed
    framed_quotes = {}
    for qt in cl.quotes.values():
        # Compute the starting time, ending time, time span, etc
        qt.compute_attrs()
        # If the Quote intersects with the requested time window, then include it
        if (start <= qt.start <= end) or (qt.start <= start <= qt.end):
            framed_quote = frame_quote(qt, start, end)
            # This check is in case a Quote starts before 'start', ends after 'end', but has no
            # occurrences between 'start' and 'end' (in which case 'framed_quote' is empty)
            if framed_quote != None:
                framed_quotes[qt.id] = framed_quote
    
    # Create the new framed Cluster
    n_quotes = len(framed_quotes)
    tot_freq = sum([qt.tot_freq for qt in framed_quotes.values()])
    framed_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq, root=cl.root, cl_id=cl.id)
    framed_cluster.quotes = framed_quotes
    
    return framed_cluster


def frame_quote(qt, start, end):
    """Cut off quote occurrences in a Quote at the specified boundaries.
    
    Arguments:
      * qt: the Quote to work on
      * start: time (in seconds from epoch) of the beginning of the target time window
      * end: time (in seconds from epoch) of the end of the target time window
    
    Returns: a new framed Quote.
    """
    
    # Frame the Timeline of the Quote
    framed_times = frame_timeline(qt, start, end)
    # Check its not empty
    if len(framed_times) == 0:
        return None
    # Then create the new framed Quote
    n_urls = len(set(framed_times))
    tot_freq = len(framed_times)
    framed_qt = ds_mt.Quote(n_urls=n_urls, tot_freq=tot_freq, string=qt.string, qt_id=qt.id)
    framed_qt.url_times = framed_times
    framed_qt.current_idx = tot_freq
    
    # And compute its attributes
    framed_qt.compute_attrs()
    
    return framed_qt


def frame_timeline(tm, start, end):
    """Cut off quote occurrences in a Timeline at the specified boundaries.
    
    Arguments:
      * tm: the Timeline to work on
      * start: time (in seconds from epoch) of the beginning of the target time window
      * end: time (in seconds from epoch) of the end of the target time window
    
    Returns: a new framed Timeline.
    """
    
    # Careful to return a copy, otherwise we just get a particular view of the same memory space,
    # which is bad for further modifications
    return tm.url_times[np.where((start <= tm.url_times) * (tm.url_times <= end))].copy()


def find_max_24h_window(timeline, prec=30*60):
    """Find the 24h window of maximum activity in a Timeline.
    
    Arguments:
      * timeline: the Timeline to scan
    
    Optional arguments:
      * prec: the precision (in seconds) of the position of the returned time window. Defaults to half an hour.
    
    Returns: the time (in seconds from epoch) of the beginning of the maximum activity window. 
    """
    
    # How many windows are we testing
    n_windows = int(np.ceil(2*86400/prec))
    
    # Compute the Timeline attributes
    if not timeline.attrs_computed:
        timeline.compute_attrs()
    
    # Get the first estimation of where the maximum is;
    # it has a precision of 1 day (see details of Timeline.compute_attrs())
    base_time = timeline.max_ipd_x_secs - 86400
    # Set the starting times of the time windows we're testing
    start_times = np.arange(n_windows)*prec + base_time
    
    # Compute activity for each time window
    ipd_all = np.zeros(n_windows)
    for i, st in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1, (st, st+86400))[0][0]
    
    # And get the max
    return start_times[np.argmax(ipd_all)]


def build_timebags(cluster, n_bags):
    """Build a number of TimeBags from a Cluster.
    
    Arguments:
      * cluster: the Cluster to work on
      * n_bags: the number of TimeBags to chop the Cluster into
    
    Returns: a list of TimeBags.
    """
    
    # Build the Timeline for the Cluster, set the parameters for the TimeBags
    cluster.build_timeline()
    step = int(round(cluster.timeline.span.total_seconds() / n_bags))
    cl_start = cluster.timeline.start
    
    # Create the sequence of TimeBags
    timebags = []
    for i in xrange(n_bags):
        timebags.append(ds_mt.TimeBag(cluster, cl_start + i*step, cl_start + (i+1)*step))
    
    return timebags


def build_n_quotes_to_clusterids(clusters):
    """Build a dictionary associating number of Quotes to Cluster ids having that number of quotes.
    
    Arguments:
      * The dict of Clusters to work on
    
    Returns: the dict of 'number of Quotes' -> 'sequence of Cluster ids'.
    """
    
    # Self-explanatory
    inv_cl_lengths = {}
    for cl in clusters.values():
        if inv_cl_lengths.has_key(cl.n_quotes):
            inv_cl_lengths[cl.n_quotes].append(cl.id)
        else:
            inv_cl_lengths[cl.n_quotes] = [cl.id]
    
    return inv_cl_lengths


def build_quotelengths_to_n_quote(clusters):
    """Build a dict associating Quote string lengths to the number of Quotes having that string length.
    
    Arguments:
      * The dict of Clusters to work on
    
    Returns: the dict of 'Quote string lengths' -> 'number of Quotes having that string length'.
    """
    
    # Self-explanatory
    inv_qt_lengths = {}
    for cl in clusters.values():
        for qt in cl.quotes.values():
            n_words = len(word_tokenize(qt.string.lower()))
            if inv_qt_lengths.has_key(n_words):
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1
    
    return inv_qt_lengths
