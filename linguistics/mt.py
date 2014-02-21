#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute word frequencies based on the MemeTracker dataset.

Word frequencies are computed for words lemmatized once with the
TreeTagger tagger.

"""


from __future__ import division

from datainterface.redistools import RedisReader
from .treetagger import get_tagger
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
