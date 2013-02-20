#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The base classes for data representation on top of which other packages
build."""


from __future__ import division

from datetime import datetime
from warnings import warn

import numpy as np
import pylab as pl

from datainterface.timeparsing import isostr_to_epoch_mt

# "import mine.filters as m_fi" has been moved into TimeBag.__init__
# to prevent a circular import problem
# see http://docs.python.org/faq/programming.html#what-are-the-best-practices-
# for-using-import-in-a-module for more details.


class TimelineBase(object):

    """Hold a series of occurrences (e.g. occurrences of a quote, or of quotes
    related to a same cluster).

    This class is used for plotting evolution of a Quote or a Cluster, or for
    analyzing the rate of activity of a Quote or Cluster. It is also a parent
    class of Quote. Times in the Timeline are usually stored in seconds from
    epoch.

    Parameters
    ----------
    length : int
        Length to Initialize the Timeline with.

    Attributes
    ----------
    attrs_computed : bool
        Whether or not :meth:`compute_attrs` has been called yet.
    start : int
        Time of the first occurrence.
    end : int
        Time of the last occurrence.
    span : int
        Span (in seconds) of the timeline.
    span_days : int
        span (in days) of the timeline (minimum 1, and rounded to nearest \
                integer).
    ipd : list of ints
        Number of occurrences per day.
    ipd_x_secs : list of ints
        The corresponding timestamps for number of occurrences per day (they \
                are the times of the middles of the days used as bins for \
                ``self.ipd``).
    argmax_ipd : int
        Index of maximum number of occurrences per day (index in ``self.ipd``).
    max_ipd : int
        Maximum number of occurrences per day.
    max_ipd_x_secs : int
        Corresponding timestamp for the maximum number of occurrences per day.

    Methods
    -------
    add_url()
        Add an url to the timeline.
    compute_attrs()
        Compute a histogram of the occurrences as well as a few useful \
                pieces of information.

    See Also
    --------
    QuoteBase

    """

    def __init__(self, length):
        """Initialize the Timeline with a certain length.

        Parameters
        ----------
        length : int
            Length to Initialize the Timeline with.

        """

        self.url_times = np.zeros(length)
        self.current_idx = 0
        self.attrs_computed = False

    def compute_attrs(self):
        """Compute a histogram of the occurrences as well as a few useful
        pieces of information.

        The useful pieces of information are:

        * starting and ending time of the Timeline
        * span in seconds and in days
        * histogram with 1-day-wide bins
        * maximum activity (instances per day: ipd)
        * 24h window of maximum activity, with a rough precision of one day
          (max_ipd_secs)

        See the :class:`class documentation <TimelineBase>` for details on
        the attributes created by this method.

        """

        if self.current_idx != len(self.url_times):
            warn(('The number of urls entered (={}) is not equal to the '
                  'number of urls allocated for (={}) when you created '
                  'this timeline object. There must be a problem '
                  'somewhere').format(self.current_idx, len(self.url_times)))

        if not self.attrs_computed:

            # Start, end, and time span of the quote.

            self.start = self.url_times.min()
            self.end = self.url_times.max()
            self.span = (datetime.fromtimestamp(self.end) -
                         datetime.fromtimestamp(self.start))
            self.span_days = max(1, int(round(self.span.total_seconds() /
                                              86400)))

            # Histogram, and maximum instances-per-day (i.e. highest spike).

            self.ipd, bins = pl.histogram(self.url_times, self.span_days)
            self.ipd_x_secs = (bins[:-1] + bins[1:]) // 2
            self.argmax_ipd = np.argmax(self.ipd)
            self.max_ipd = self.ipd[self.argmax_ipd]
            self.max_ipd_x_secs = self.ipd_x_secs[self.argmax_ipd]

            self.attrs_computed = True

    def add_url(self, line_fields):
        """Add an url to the Timeline.

        Parameters
        ----------
        line_fields : list of strings
            The fields extracted from the MemeTracker dataset file.

        """

        for i in xrange(int(line_fields[3])):

            self.url_times[self.current_idx] = \
                int(isostr_to_epoch_mt(line_fields[2]))
            self.current_idx += 1


class QuoteBase(TimelineBase):

    """Hold a quote, its attributes, and its timeline (this is a subclass of
    Timeline).

    This is a subclass of Timeline, meant to hold additionnal information
    about a quote.

    The constructor accepts either the `line_fields` parameter,
    OR all of `n_urls`, `tot_freq`, `string`, and `qt_id` (those four
    parameters correspond to the extracted data from `line_fields`). Any other
    combination of parameters will raise a ValueError.

    Parameters
    ----------
    line_fields : list of strings, optional
        Fields from the MemeTracker dataset file, as provided by
        :meth:`datainterface.mt.ClustersLoader.handle_quote`.
    n_urls : int, optional
        Number of urls quoting the quote.
    tot_freq : int, optional
        Total number of occurrences of the quote.
    string : string, optional
        The quote string itself.
    qt_id : int, optional
        The quote id, as given by the dataset.

    Raises
    ------
    ValueError
        If the parameters to the constructor are not either only
        `line_fields`, or all of `n_urls`, `tot_freq`, `string`, `qt_id`.

    Methods
    -------
    to_qt_string_lower()
        Build a :class:`full.QtString` from this Quote, in lowercase.

    """

    def __init__(self, line_fields=None, n_urls=None, tot_freq=None,
                 string=None, qt_id=None):
        """Initialize the quote based on a line from the dataset, or explicit
        attributes.

        The constructor accepts either the `line_fields` parameter,
        OR all of `n_urls`, `tot_freq`, `string`, and `qt_id` (those four
        parameters correspond to the extracted data from `line_fields`). Any
        other combination of parameters will raise a ValueError.

        Parameters
        ----------
        line_fields : list of strings, optional
            Fields from the MemeTracker dataset file, as provided by
            :meth:`datainterface.mt.ClustersLoader.handle_quote`.
        n_urls : int, optional
            Number of urls quoting the quote.
        tot_freq : int, optional
            Total number of occurrences of the quote.
        string : string, optional
            The quote string itself.
        qt_id : int, optional
            The quote id, as given by the dataset.

        Raises
        ------
        ValueError
            If the parameters to the constructor are not either only
            `line_fields`, or all of `n_urls`, `tot_freq`, `string`, `qt_id`.

        """

        if line_fields != None:
            if (n_urls != None or tot_freq != None or
                string != None or qt_id != None):

                raise ValueError(('Bad set of arguments when creating this '
                                  'quote. You must specify either '
                                  '"line_fields" (={}) OR all of "n_urls"'
                                  ' (={}), "tot_freq" (={}), "string" (={}), '
                                  'and "qt_id" (={}).').format(line_fields,
                                                               n_urls,
                                                               tot_freq,
                                                               string, qt_id))

            self.n_urls = int(line_fields[2])
            self.tot_freq = int(line_fields[1])
            self.string = line_fields[3]
            self.string_length = len(self.string)
            self.id = line_fields[4]

        else:

            if (n_urls == None or tot_freq == None or
                string == None or qt_id == None):

                raise ValueError(('Bad set of arguments when creating this '
                                  'quote. You must specify either '
                                  '"line_fields" (={}) OR all of "n_urls"'
                                  ' (={}), "tot_freq" (={}), "string" (={}), '
                                  'and "qt_id" (={}).').format(line_fields,
                                                               n_urls,
                                                               tot_freq,
                                                               string, qt_id))

            self.n_urls = n_urls
            self.tot_freq = tot_freq
            self.string = string
            self.string_length = len(string)
            self.id = qt_id

        super(QuoteBase, self).__init__(self.tot_freq)

    def __repr__(self):
        """Define how we see a Quote object when printed in a terminal
        (e.g. ``>>> myquote``)."""

        return '<Quote: ' + self.__unicode__() + '>'

    def __str__(self):
        """See :meth:`__unicode__`."""

        return self.__unicode__()

    def __unicode__(self):
        """Define how we see a Quote object when printed with ``print``
        (e.g. ``>>> print myquote``)."""

        return ('"' + self.string + '" (quote #{} ; '
                'tot_freq={})').format(self.id, self.tot_freq)


class ClusterBase(object):

    """Hold a cluster, its attributes, its quotes, and if necessary its
    Timeline.

    Data is loaded into the structure after creation (as the dataset file is
    read), and can be analyzed later thanks to methods imported from analysis
    packages.

    The constructor accepts either the `line_fields` parameter,
    OR all of `n_quotes`, `tot_freq`, `root`, and `cl_id` (those four
    parameters correspond to the extracted data from `line_fields`). Any other
    combination of parameters will raise a ValueError.

    Parameters
    ----------
    line_fields : list of strings, optional
        Fields from the MemeTracker dataset file, as provided by
        :meth:`datainterface.mt.ClustersLoader.handle_quote`.
    n_quotes : int, optional
        Number of quotes in the cluster.
    tot_freq : int, optional
        Total number of occurrences in the cluster (i.e. sum of the
        ``tot_freq``\ s of the quotes).
    root : string, optional
        The root string for the cluster.
    cl_id : int, optional
        The cluster id, as given by the dataset.

    Raises
    ------
    ValueError
        If the parameters to the constructor are not either only
        `line_fields`, or all of `n_quotes`, `tot_freq`, `root`, `cl_id`.

    Attributes
    ----------
    timeline : :class:`~full.Timeline`
        The built timeline of the cluster. Created by :meth:`build_timeline`.
    timeline_built : bool
        Whether or not :meth:`build_timeline` has been called.

    Methods
    -------
    add_quote()
        Add a :class:`~full.Quote` to the cluster (used when loading the data \
                into the :class:`~full.Cluster` object).
    build_timeline()
        Build the :class:`~full.Timeline` representing the occurrences of the \
                cluster as a single object (not categorized into quotes; \
                this is used to plot the occurrences of the cluster).

    See Also
    --------
    TimelineBase, full.Timeline, QuoteBase, full.Quote

    """

    def __init__(self, line_fields=None, n_quotes=None, tot_freq=None,
                 root=None, cl_id=None):
        """Initialize the cluster based on a line from the dataset, or
        explicit attributes.

        The constructor accepts either the `line_fields` parameter,
        OR all of `n_quotes`, `tot_freq`, `root`, and `cl_id` (those four
        parameters correspond to the extracted data from `line_fields`). Any
        other combination of parameters will raise a ValueError.

        Parameters
        ----------
        line_fields : list of strings, optional
            Fields from the MemeTracker dataset file, as provided by
            :meth:`datainterface.mt.ClustersLoader.handle_quote`.
        n_quotes : int, optional
            Number of quotes in the cluster.
        tot_freq : int, optional
            Total number of occurrences in the cluster (i.e. sum of the
            ``tot_freq``\ s of the quotes).
        root : string, optional
            The root string for the cluster.
        cl_id : int, optional
            The cluster id, as given by the dataset.

        Raises
        ------
        ValueError
            If the parameters to the constructor are not either only
            `line_fields`, or all of `n_quotes`, `tot_freq`, `root`, `cl_id`.

        """

        if line_fields != None:
            if (n_quotes != None or tot_freq != None or
                root != None or cl_id != None):

                raise ValueError(('Bad set of arguments when creating this '
                                  'cluster. You must specify either '
                                  '"line_fields" (={}) OR all of "n_quotes" '
                                  '(={}), "tot_freq" (={}), "root" (={}), '
                                  'and "cl_id" (={}).').format(line_fields,
                                                               n_quotes,
                                                               tot_freq,
                                                               root,
                                                               cl_id))

            self.n_quotes = int(line_fields[0])
            self.tot_freq = int(line_fields[1])
            self.root = line_fields[2]
            self.root_length = len(self.root)
            self.id = int(line_fields[3])

        else:
            if (n_quotes == None or tot_freq == None or
                root == None or cl_id == None):

                raise ValueError(('Bad set of arguments when creating this '
                                  'cluster. You must specify either '
                                  '"line_fields" (={}) OR all of "n_quotes" '
                                  '(={}), "tot_freq" (={}), "root" (={}), '
                                  'and "cl_id" (={}).').format(line_fields,
                                                               n_quotes,
                                                               tot_freq,
                                                               root,
                                                               cl_id))

            self.n_quotes = n_quotes
            self.tot_freq = tot_freq
            self.root = root
            self.root_length = len(root)
            self.id = cl_id

        self.quotes = {}
        self.timeline_built = False

    def __repr__(self):
        """Define how we see a Cluster object when printed in a terminal
        (e.g. ``>>> mycluster``)."""

        return '<Cluster: ' + self.__unicode__() + '>'

    def __str__(self):
        """See :meth:`__unicode__`."""

        return self.__unicode__()

    def __unicode__(self):
        """Define how we see a Cluster object when printed with ``print``
        (e.g. ``>>> print mycluster``)."""

        return ('"' + self.root + '" (cluster #{} ; tot_quotes={} ; '
                'tot_freq={})').format(self.id, self.n_quotes, self.tot_freq)

    def build_timeline(self):
        """Build the Timeline representing the occurrences of the cluster as a
        single object (used in 'plot').

        The :class:`full.Timeline` object is stored in ``self.timeline``, and
        its attributes are automatically computed.

        """

        from datastructure.full import Timeline

        if not self.timeline_built:

            self.timeline = Timeline(self.tot_freq)

            for qt in self.quotes.values():

                idx = self.timeline.current_idx
                self.timeline.url_times[idx:idx + qt.tot_freq] = qt.url_times
                self.timeline.current_idx += qt.tot_freq

            self.timeline.compute_attrs()
            self.timeline_built = True


class TimeBagBase(object):

    """A bag of strings with some attributes, resulting from the splitting of
    a Cluster (or Quote) into time windows.

    This object is used for analysis of the evolution of a Cluster through
    time.

    Methods:
      * __init__: build the TimeBag from a Cluster, a starting time, and an
                  ending time
     * qt_string_lower: return a QtString corresponding to string number k of
                         the Timebag, in lowercase

    """

    def __init__(self, cluster, start, end):
        """Build the TimeBag from a Cluster, a starting time, and an ending
        time.

        A TimeBag containing all strings occurring between start and end will
        be created. Attributes about the occurrences are also stored: their
        tot_freqs, their number of urls, and their ids. The id of the parent
        Cluster is kept, the total frequency of the TimeBag if computed, and
        the string with highest frequency is found too.

        Arguments:
          * cluster: the Cluster from which to build the TimeBag
          * start: starting time for the TimeBag, in seconds from epoch
          * end: ending time for the TimeBag, in seconds from epoch

        """

        # This import goes here to prevent a circular import problem.

        import mine.filters as m_fi

        framed_cluster = m_fi.frame_cluster(cluster, start, end)

        self.id_fromcluster = cluster.id
        self.strings = []

        if framed_cluster:

            self.tot_freq = framed_cluster.tot_freq
            self.tot_freqs = np.zeros(framed_cluster.n_quotes)
            self.n_urlss = np.zeros(framed_cluster.n_quotes)
            self.ids = np.zeros(framed_cluster.n_quotes)

            for i, qt in enumerate(framed_cluster.quotes.values()):

                self.strings.append(qt.string)
                self.tot_freqs[i] = qt.tot_freq
                self.n_urlss[i] = qt.n_urls
                self.ids[i] = qt.id

            self.argmax_freq_string = np.argmax(self.tot_freqs)
            self.max_freq_string = self.strings[self.argmax_freq_string]

        else:

            self.tot_freq = 0
            self.tot_freqs = []
            self.n_urlss = []
            self.ids = []
            self.argmax_freq_string = -1
            self.max_freq_string = ''
