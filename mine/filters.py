#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Filter and frame the cluster data for future mining.

The clusters in the MemeTracker dataset may need some cleaning up: some of them
are not in English, some of them contain too few quotes, and one may want to
frame them around their peak activity to make sure only really relevant quotes
are included. This module allows for such preprocessing of the cluster data.

"""


from __future__ import division

import numpy as np

from linguistics.treetagger import get_tagger
from linguistics.language import langdetect


def frame_cluster_around_peak(cl, span_before=2 * 86400, span_after=2 * 86400):
    """Cut off quote occurrences in a :class:`~datastructure.full.Cluster`
    around the 24h window with maximum activity.

    Parameters
    ----------
    cl : :class:`~datastructure.full.Cluster`
        The cluster to work on
    span_before : int, optional
        Time span (in seconds) to include before the beginning of the max 24h
        window; defaults to 2 days.
    span_after : int, optional
        Time span (in seconds) to include after the end of the max 24h window;
        defaults to 2 days.

    Returns
    -------
    Cluster
        A new framed :class:`~datastructure.full.Cluster`.

    See Also
    --------
    datastructure.full.Cluster, frame_cluster

    """

    cl.build_timeline()
    max_24h = find_max_24h_window(cl.timeline)

    start = max_24h - span_before
    end = max_24h + 86400 + span_after

    return frame_cluster(cl, start, end)


def frame_cluster(cl, start, end):
    """Cut off quote occurrences in a :class:`~datastructure.full.Cluster` at
    the specified boundaries.

    Parameters
    ----------
    cl : :class:`~datastructure.full.Cluster`
        The cluster to work on.
    start : int
        Time (in seconds from epoch) of the beginning of the target time
        window.
    end : int
        Time (in seconds from epoch) of the end of the target time window.

    Returns
    -------
    Cluster
        A new framed :class:`~datastructure.full.Cluster`; if no quotes were
        left after framing, `None` is returned.

    See Also
    --------
    datastructure.full.Cluster

    """

    import datastructure.full as ds_mt

    framed_quotes = {}

    for qt in cl.quotes.itervalues():

        # Compute the starting time, ending time, time span, etc.

        qt.compute_attrs()

        # If the Quote intersects with the requested time window, include it.

        if (start <= qt.start <= end) or (qt.start <= start <= qt.end):

            framed_quote = frame_quote(qt, start, end)

            # If the Quote starts before 'start', ends after 'end', but has no
            # occurrences between 'start' and 'end' (in which case
            # 'framed_quote' is empty), exclude it.

            if framed_quote is not None:
                framed_quotes[qt.id] = framed_quote

    # If no quotes were kept, return None.

    if len(framed_quotes) == 0:
        return None

    # Else, create the new framed Cluster.

    n_quotes = len(framed_quotes)
    tot_freq = sum([qt.tot_freq for qt in framed_quotes.values()])
    framed_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq,
                                   root=cl.root, cl_id=cl.id)
    framed_cluster.quotes = framed_quotes

    return framed_cluster


def frame_quote(qt, start, end):
    """Cut off quote occurrences in a :class:`~datastructure.full.Quote`
    at the specified boundaries.

    Parameters
    ----------
    qt : :class:`~datastructure.full.Quote`
        The quote to work on.
    start : int
        Time (in seconds from epoch) of the beginning of the target time
        window.
    end : int
        Time (in seconds from epoch) of the end of the target time window.

    Returns
    -------
    Quote
        A new framed :class:`~datastructure.full.Quote`.

    See Also
    --------
    datastructure.full.Quote

    """

    import datastructure.full as ds_mt

    # Frame the Timeline of the Quote.

    framed_times = frame_timeline(qt, start, end)

    # Check its not empty.

    if len(framed_times) == 0:
        return None

    # Then create the new framed Quote.

    n_urls = len(set(framed_times))
    tot_freq = len(framed_times)
    framed_qt = ds_mt.Quote(n_urls=n_urls, tot_freq=tot_freq,
                            string=qt.string, qt_id=qt.id)
    framed_qt.url_times = framed_times
    framed_qt.current_idx = tot_freq

    # And compute its attributes.

    framed_qt.compute_attrs()

    return framed_qt


def frame_timeline(tm, start, end):
    """Cut off quote occurrences in a :class:`~datastructure.full.Timeline`
    at the specified boundaries.

    Parameters
    ----------
    tm : :class:`~datastructure.full.Timeline`
        The timeline to work on.
    start : int
        Time (in seconds from epoch) of the beginning of the target time
        window.
    end : int
        Time (in seconds from epoch) of the end of the target time window.

    Returns
    -------
    Timeline
        A new framed :class:`~datastructure.full.Timeline`.

    See Also
    --------
    datastructure.full.Timeline

    """

    # Careful to return a copy, otherwise we just get a particular view of
    # the same memory space, which is bad for further modifications.

    return tm.url_times[np.where((start <= tm.url_times) *
                                 (tm.url_times <= end))].copy()


def find_max_24h_window(timeline, prec=30 * 60):
    """Find the 24h window of maximum activity in a
    :class:`~datastructure.full.Timeline`.

    Parameters
    ----------
    timeline : :class:`~datastructure.full.Timeline`
        The timeline to scan.
    prec : int, optional
        The precision (in seconds) of the position of the returned time
        window; defaults to half an hour.

    Returns
    -------
    int
        The time (in seconds from epoch) of the beginning of the maximum
        activity window.

    See Also
    --------
    datastructure.full.Timeline

    """

    # How many windows are we testing.

    n_windows = int(np.ceil(2 * 86400 / prec))

    # Compute the Timeline attributes.

    timeline.compute_attrs()

    # First estimation of where the maximum is; it has a precision of 1 day
    # (see details of Timeline.compute_attrs()).

    base_time = timeline.max_ipd_x_secs - 86400

    # Starting times of the time windows we're testing.

    start_times = np.arange(n_windows) * prec + base_time

    # Compute activity for each time window.

    ipd_all = np.zeros(n_windows)

    for i, stt in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1,
                                  (stt, stt + 86400))[0][0]

    # And get the max.

    return start_times[np.argmax(ipd_all)]


def filter_cluster(cl, min_tokens, max_days):
    """Filter a :class:`~datastructure.full.Cluster` to keep only English
    quotes longer than `min_tokens` and spanning less than `max_days`, with the
    final cluster spanning less than `max_days`.

    Parameters
    ----------
    cl : :class:`~datastructure.full.Cluster`
        The cluster to filter.
    min_tokens : int
        The minimum required number of words to keep a quote.
    max_days : int
        The maximum span (in days) required to keep a quote or a cluster.

    Returns
    -------
    Cluster
        A new cluster (referencing the old quotes, not newly created ones) with
        only the quotes that have more than `min_tokens` tokens, span less than
        `max_days`, and that were detected to be in English; if the root of the
        cluster had less than `min_tokens`, if it was not detected as being
        English, if no quotes inside the cluster were kept, or if the
        post-filter cluster spanned more than `max_days`, `None` is returned.

    """

    import datastructure.full as ds_mt
    tagger = get_tagger()

    # If the root has less tokens than wanted, filter the whole cluster.
    if (len(tagger.Tokenize(cl.root)) < min_tokens
            or langdetect(cl.root) != 'en'):
        return None

    # Else, examine each quote for min_tokens, max_days, and language
    filtered_quotes = {}
    for qt in cl.quotes.itervalues():

        qt.compute_attrs()
        if (len(tagger.Tokenize(qt.string)) >= min_tokens and
                qt.span_days <= max_days
                and langdetect(qt.string) == 'en'):
            filtered_quotes[qt.id] = qt

    # If no quotes where kept, filter the whole cluster.
    if len(filtered_quotes) == 0:
        return None

    # Else, create the new filtered Cluster.
    n_quotes = len(filtered_quotes)
    tot_freq = sum([qt.tot_freq for qt in filtered_quotes.values()])
    filtered_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq,
                                     root=cl.root, cl_id=cl.id)
    filtered_cluster.quotes = filtered_quotes

    # Finally, if the new cluster spans too many days, discard it.
    filtered_cluster.build_timeline()
    if filtered_cluster.timeline.span_days > max_days:
        return None

    return filtered_cluster
