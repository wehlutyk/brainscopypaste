#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute basic statistics on the MemeTracker dataset to get an idea of what
it looks like."""


from __future__ import division

from linguistics.treetagger import get_tagger


def build_n_quotes_to_clusterids(clusters):
    """Build a dictionary associating number of
    :class:`~datastructure.full.Quote`\ s to
    :class:`~datastructure.full.Cluster` ids having that number of quotes.

    This can then be used to compute the distribution of number of quotes per
    cluster, as in :mod:`mine_statistics`.

    Parameters
    ----------
    clusters : dict or :class:`~datainterface.redistools.RedisReader`
        The dict of :class:`~datastructure.full.Cluster`\ s to work on (can
        also be a Redis connection behaving like a dict).

    Returns
    -------
    dict
        The association of `number of quotes` to `list of cluster ids having
        that many quotes`.

    See Also
    --------
    mine_statistics

    """

    inv_cl_lengths = {}

    for cl_id, cl in clusters.iteritems():

        if cl.n_quotes in inv_cl_lengths:
            inv_cl_lengths[cl.n_quotes].append(cl_id)
        else:
            inv_cl_lengths[cl.n_quotes] = [cl_id]

    return inv_cl_lengths


def build_quotelengths_to_n_quote(clusters):
    """Build a dict associating :class:`~datastructure.full.Quote` string
    lengths to the number of :class:`~datastructure.full.Quotes` having that
    string length.

    This amounts to the distribution of quote string lengths.

    Parameters
    ----------
    clusters : dict or :class:`~datainterface.redistools.RedisReader`
        The dict of :class:`~datastructure.full.Cluster`\ s to work on (can
        also be a Redis connection behaving like a dict).

    Returns
    -------
    dict
        The association of `quote string length` to `number of quotes having
        that string length`.

    See Also
    --------
    mine_statistics

    """

    tagger = get_tagger()

    inv_qt_lengths = {}

    for cl in clusters.itervalues():

        for qt in cl.quotes.itervalues():

            n_words = len(tagger.Tokenize(qt.string.lower()))

            if n_words in inv_qt_lengths:
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1

    return inv_qt_lengths
