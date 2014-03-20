#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute word frequencies based on the MemeTracker dataset.

Word frequencies are computed for words lemmatized once with the
TreeTagger tagger.

"""


from __future__ import division

import datainterface.picklesaver as ps
from datainterface.redistools import RedisReader
from .treetagger import get_tagger
from datainterface.fs import get_filename, check_file
import settings as st


def load_clusters():
    """Connect to redis and load the pre-filtered clusters.

    Returns
    -------
    RedisReader
        A :class:`~datainterface.redistools.RedisReader` instance.

    See Also
    --------
    compute_word_frequencies

    """

    print
    print 'Connecting to redis server for cluster data...',

    clusters = RedisReader(st.redis_mt_clusters_filtered_pref)

    print 'OK'

    return clusters


def compute_word_frequencies():
    """Load clusters and compute word frequencies extracted from the clusters.

    Quotes in the dataset are first lemmatized, then frequencies are counted.

    Returns
    -------
    dict
        The association of each word to its absolute frequency.

    """

    # Load clusters
    clusters = load_clusters()

    # Prepare
    freqs = {}
    tagger = get_tagger()

    print 'Computing word frequencies based on MemeTracker...',

    # For each cluster
    for cluser_id, cluster in clusters.iteritems():

        # For each quote
        for quote_id, quote in cluster.quotes.iteritems():

            # Lemmatize
            lems = tagger.Lemmatize(quote.string)

            # And count each lemma as many times as the quote's frequency
            for lem in lems:
                try:
                    freqs[lem] += quote.tot_freq
                except KeyError:
                    freqs[lem] = quote.tot_freq

    print 'OK'

    return freqs


def compute_word_frequencies_start_quotes(bargs):
    """Load clusters and compute word frequencies extracted from the clusters,
    keeping only those quotes involved as start quotes in substitutions.

    Quotes in the dataset are first lemmatized, skipped if they're not
    involved as a start quote in a substitution, then frequencies are counted.

    Parameters
    ----------
    bargs : :class:`~baseargs.BaseArgs` instance
        The argument set defining which mined substitutions to use.

    Returns
    -------
    dict
        The association of each word to its absolute frequency.

    """

    # The data we're reading
    clusters = load_clusters()
    subs_filename = get_filename(bargs)
    check_file(subs_filename, for_read=True)
    substitutions = ps.load(subs_filename)
    start_quote_ids = set([int(s.mother.qt_id) for s in substitutions])

    # Prepare
    start_freqs = {}
    tagger = get_tagger()

    print ('Computing word frequencies in start quotes involved '
           'in substitutions in MemeTracker...'),

    # For each cluster
    for cluser_id, cluster in clusters.iteritems():

        # For each quote
        for quote_id, quote in cluster.quotes.iteritems():

            # We only want words from quotes involved as
            # starts in substitutions
            if int(quote_id) not in start_quote_ids:
                continue

            # Lemmatize
            lems = tagger.Lemmatize(quote.string)

            # And count each lemma as many times as the quote's frequency
            for lem in lems:
                try:
                    start_freqs[lem] += quote.tot_freq
                except KeyError:
                    start_freqs[lem] = quote.tot_freq

    print 'OK'

    return start_freqs
