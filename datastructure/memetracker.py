#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hold data from the MemeTracker dataset like Clusters, Quotes, Timelines,
and TimeBags.

Classes:
  * Timeline: hold a series of occurences (e.g. occurences of a quote, or of
              quotes related to a same cluster)
  * Quote: hold a quote, its attributes, and its timeline (this is a subclass
           of Timeline)
  * Cluster: hold a cluster, its attributes, its quotes, and if necessary its
             Timeline
  * QtString: augment a string with POS tags, tokens, cluster id and quote id
  * TimeBag: a bag of strings with some attributes, resulting from the
             splitting of a Cluster (or Quote) into time windows

"""


from __future__ import division

from datetime import datetime
from warnings import warn
import textwrap

import numpy as np
import pylab as pl

from datainterface.timeparsing import isostr_to_epoch_mt
import visualize.memetracker as v_mt
import visualize.annotations as v_an
import linguistics.memetracker as l_mt
from linguistics.treetagger import TreeTaggerTags
import settings as st

# "import analyze.memetracker as a_mt" has been moved into TimeBag.__init__
# to prevent a circular import problem
# see http://docs.python.org/faq/programming.html#what-are-the-best-practices-
# for-using-import-in-a-module for more details.


class Timeline(object):
    
    """Hold a series of occurrences (e.g. occurrences of a quote, or of quotes
    related to a same cluster).
    
    This class is used for plotting evolution of a Quote or a Cluster, or for
    analyzing the rate of activity of a Quote or Cluster. It is also a parent
    class of Quote. Times in the Timeline are usually stored in seconds from
    epoch.
    
    Methods:
      * __init__: initialize the Timeline with a certain length
      * compute_attrs: compute a histogram of the occurrences as well as a few
                       useful pieces of information
      * add_url: add an url to the timeline
      * plot: plot the Timeline
      * bar: plot the bar-chart of the Timeline
    
    """
    
    def __init__(self, length):
        """Initialize the Timeline with a certain length."""
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
        """Add an url to the Timeline."""
        for i in xrange(int(line_fields[3])):
            
            self.url_times[self.current_idx] = \
                int(isostr_to_epoch_mt(line_fields[2]))
            self.current_idx += 1
    
    def plot(self, smooth_res=5):
        """Plot the Timeline."""
        v_mt.plot_timeline(self, smooth_res=smooth_res)
    
    def barflow(self, bins=25):
        """Plot the bar-chart of the Timeline."""
        return v_mt.barflow_timeline(self, bins)


class Quote(Timeline):
    
    """Hold a quote, its attributes, and its timeline (this is a subclass of
    Timeline).
    
    This is a subclass of Timeline, meant to hold additionnal information
    about a quote.
    
    Methods:
      * __init__: initialize the quote based on a line from the dataset, or
                  explicit attributes
      * __repr__: define how we see a Quote object when printed in a terminal
                  (e.g. >>> myquote)
      * __str__: see __unicode__
      * __unicode__: define how we see a Quote object when printed with print
                     (e.g. >>> print myquote)
      * to_qt_string_lower: return a QtString built from this Quote, in
                            lowercase
      * plot: plot the time evolution of the Quote (with a legend)
      * bar: plot the bar-chart of the Quote
    
    """
    
    def __init__(self, line_fields=None, n_urls=None, tot_freq=None,
                 string=None, qt_id=None):
        """Initialize the quote based on a line from the dataset, or explicit
        attributes.
        
        Arguments -- either line_fields OR all of n_urls, tot_freq, string,
                     and qt_id must be provided:
          * line_fields: a list of strings read from tab-separated fields in
                         the raw dataset file, as provided by methods in
                         'datainterface.memetracker'
          * n_urls: number of urls quoting the quote
          * tot_freq: total number of occurrences of the quote
          * string: the quote string itself
          * qt_id: the quote id, as given by the dataset
        
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
        
        super(Quote, self).__init__(self.tot_freq)
    
    def __repr__(self):
        """Define how we see a Quote object when printed in a terminal
        (e.g. >>> myquote)."""
        return '<Quote: ' + self.__unicode__() + '>'
    
    def __str__(self):
        """See __unicode__."""
        return self.__unicode__()
    
    def __unicode__(self):
        """Define how we see a Quote object when printed with print
        (e.g. >>> print myquote)."""
        return ('"' + self.string + '" (quote #{} ; '
                'tot_freq={})').format(self.id, self.tot_freq)
    
    def to_qt_string_lower(self, cl_id, parse=True):
        """Return a QtString built from this Quote, in lowercase."""
        return QtString(self.string.lower(), cl_id, self.id, parse=parse)
    
    def plot(self, smooth_res=5):
        """Plot the time evolution of the Quote (with a legend).
        
        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution can
                        be additionally plotted; this is the width, in days,
                        of that moving average. If -1 is given, no moving
                        average is plotted. Defaults to 5 days.
        
        """
        
        v_mt.plot_timeline(self, label=self.__unicode__(),
                           smooth_res=smooth_res)
    
    def barflow(self, bins=25):
        """Plot the bar-chart of the Quote."""
        return v_mt.barflow_timeline(self, bins)


class Cluster(object):
    
    """Hold a cluster, its attributes, its quotes, and if necessary its
    Timeline.
    
    Data is loaded into the structure after creation (as the dataset file is
    read), and can be analyzed later thanks to methods imported from analysis
    packages.
    
    Methods:
      * __init__: initialize the cluster based on a line from the dataset, or
                  explicit attributes
      * __repr__: define how we see a Cluster object when printed in a
                  terminal (e.g. >>> mycluster)
      * __str__: see __unicode__
      * __unicode__: define how we see a Cluster object when printed with
                     print (e.g. >>> print mycluster)
      * add_quote: add a Quote to the Cluster (used when loading the data into
                   the Cluster object)
      * build_timeline: build the Timeline representing the occurrences of the
                        cluster as a single object (not categorized into
                        quotes; this is used to plot the occurrences of the
                        cluster)
      * build_timebags: build a number of TimeBags from the Cluster
      * plot_quotes: plot the individual Quotes of the Cluster
      * plot: plot the time evolution of the Cluster as a single Timeline
      * bar: plot the bar-chart of the Cluster Timeline
      * bar_quotes: plot the stacked bar-chart of the Quotes in the Cluster,
                    with annotations
      * bar_quotes_norm: plot the stacked bar-chart of the Quotes in the,
                         Cluster, all normalized to one, with text-less
                         annotations
      * bar_all: plot the bar-plot, stacked bar-plot, and normalized stacked
                 bar-plot for the cluster, with annotations
      * iter_substitutions_root: iterate through substitutions taken as
                                 changes from root string. Yield (mother,
                                 string or substring, bag info) tuples.
      * iter_substitutions_tbgs: iterate through substitutions taken as
                                 changes between timebags. Yield (mother,
                                 string or substring, bag info) tuples.
      * iter_substitutions_cumtbgs: iterate through substitutions taken as
                                    changes between cumulated timebags. Yield
                                    (mother, string or substring, bag info)
                                    tuples.
      * iter_substitutions_time: iterate through substitutions taken as
                                 transitions from earlier quotes to older
                                 quotes (in order of appearance in time).
    
    """
    
    def __init__(self, line_fields=None, n_quotes=None, tot_freq=None,
                  root=None, cl_id=None):
        """Initialize the cluster based on a line from the dataset, or
        explicit attributes.
        
        Arguments -- either line_fields OR all of n_quotes, tot_freq, root,
                     and cl_id must be provided:
          * line_fields: a list of strings read from tab-separated fields in
                         the raw dataset file, as provided by methods in
                         'datainterface.memetracker'
          * n_quotes: number of quotes in the cluster
          * tot_freq: total number of occurrences of the cluster (i.e. sum of
                      tot_freqs of the Quotes)
          * root: the root string for the cluster
          * cl_id: the cluster id, as given by the dataset
        
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
        self.iter_substitutions = {'root': self.iter_substitutions_root,
                                   'tbgs': self.iter_substitutions_tbgs,
                                   'cumtbgs': self.iter_substitutions_cumtbgs,
                                   'time': self.iter_substitutions_time}
    
    def __repr__(self):
        """Define how we see a Cluster object when printed in a terminal
        (e.g. >>> mycluster)."""
        return '<Cluster: ' + self.__unicode__() + '>'
    
    def __str__(self):
        """See __unicode__."""
        return self.__unicode__()
    
    def __unicode__(self):
        """Define how we see a Cluster object when printed with print
        (e.g. >>> print mycluster)."""
        return ('"' + self.root + '" (cluster #{} ; tot_quotes={} ; '
                'tot_freq={})').format(self.id, self.n_quotes, self.tot_freq)
    
    def add_quote(self, line_fields):
        """Add a Quote to the Cluster (used when loading the data into the
        Cluster object)."""
        self.quote[int(line_fields[4])] = Quote(line_fields)
    
    def build_timeline(self):
        """Build the Timeline representing the occurrences of the cluster as a
        single object (used in 'plot')."""
        if not self.timeline_built:
            
            self.timeline = Timeline(self.tot_freq)
            
            for qt in self.quotes.values():
                
                idx = self.timeline.current_idx
                self.timeline.url_times[idx:idx + qt.tot_freq] = qt.url_times
                self.timeline.current_idx += qt.tot_freq
            
            self.timeline.compute_attrs()
            self.timeline_built = True
    
    def build_timebags(self, n_bags, cumulative=False):
        """Build a number of TimeBags from the Cluster.
        
        Arguments:
          * n_bags: the number of TimeBags to build
        
        Keyword arguments:
          * cumulative: boolean specifying if the timebags built should be
                        time-cumulative or not. Defaults to False.
        
        Returns: a list of TimeBag objects
        
        """
        
        # This import goes here to prevent a circular import problem.
        
        import analyze.memetracker as a_mt
        
        return a_mt.build_timebags(self, n_bags, cumulative=cumulative)
    
    def plot_quotes(self, smooth_res=-1):
        """Plot the individual Quotes of the Cluster.
        
        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution of
                        the quotes can be additionally plotted; this is the
                        width, in days, of that moving average. If -1 is
                        given, no moving average is plotted. Defaults to -1
                        (no moving average plotted).
        
        """
        
        for qt in self.quotes.values():
            qt.plot(smooth_res=smooth_res)
        
        pl.title(self.__unicode__())
    
    def plot(self, smooth_res=5):
        """Plot the time evolution of the Cluster as a single Timeline.
        
        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution can
                        be additionally plotted; this is the width, in days,
                        of that moving average. If -1 is given, no moving
                        average is plotted. Defaults to 5 days.
        
        """
        
        self.build_timeline()
        v_mt.plot_timeline(self.timeline, label=self.__unicode__(),
                           smooth_res=smooth_res)
    
    def barflow(self, bins=25):
        """Plot the bar-chart of the Cluster Timeline."""
        self.build_timeline()
        return self.timeline.barflow(bins)
    
    def bar_quotes(self, bins=25, drawtext=True):
        """Plot the stacked bar-chart of the Quotes in the Cluster, with
        annotations."""
        return v_mt.bar_cluster(self, bins, drawtext)
    
    def flow_quotes(self, bins=25, drawtext=True):
        """Plot the flow of the stacked bar-chart of Quotes in a Cluster, with
        added annotations."""
        return v_mt.flow_cluster(self, bins, drawtext)
    
    def bar_quotes_norm(self, bins=25, drawtext=True):
        """Plot the stacked bar-chart of the Quotes in the Cluster, all
        normalized to one, with text-less annotations."""
        return v_mt.bar_cluster_norm(self, bins, drawtext)
    
    def barflow_all(self, bins=25):
        """Plot the bar-plot, stacked bar-plot, and flow of the stacked bar-
        plot for the cluster, with annotations."""
        pl.subplot(311)
        pl.title(textwrap.fill('{}'.format(self), 70))
        self.barflow(bins)
        pl.subplot(312)
        af1 = self.bar_quotes(bins, drawtext=False)[1]
        pl.subplot(313)
        af2 = self.flow_quotes(bins)[1]
        v_an.linkAnnotationFinders([af1, af2])
    
    def iter_substitutions_root(self, argset):
        """Iterate through substitutions taken as changes from root string.
        Yield (mother, string or substring, bag info) tuples."""
        return l_mt.cluster_iter_substitutions_root(self, argset)
    
    def iter_substitutions_tbgs(self, argset):
        """Iterate through substitutions taken as changes between timebags.
        Yield (mother, string or substring, bag info) tuples."""
        return l_mt.cluster_iter_substitutions_tbgs(self, argset)
    
    def iter_substitutions_cumtbgs(self, argset):
        """Iterate through substitutions taken as changes between cumulated 
        timebags. Yield (mother, string or substring, bag info) tuples."""
        return l_mt.cluster_iter_substitutions_cumtbgs(self, argset)
    
    def iter_substitutions_time(self, argset):
        """Iterate through substitutions taken as transitions from earlier
        quotes to older quotes (in order of appearance in time)."""
        return l_mt.cluster_iter_substitutions_time(self, argset)


class QtString(str):
    
    """Augment a string with POS tags, tokens, cluster id and quote id.
    
    Methods:
      * __init__: parse the string for POS tags and tokens, if asked to
    
    """
    
    tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                            TAGINENC='utf-8', TAGOUTENC='utf-8')
    
    def __new__(cls, string, cl_id=-1, qt_id=-1, parse=True):
        return super(QtString, cls).__new__(cls, string)
    
    def __init__(self, string, cl_id, qt_id, parse=True):
        """Parse the string for POS tags and tokens, if asked to ('parse'
        argument)."""
        self.cl_id = cl_id
        self.qt_id = qt_id
        if parse:
            self.POS_tags = self.tagger.Tags(string)
            self.tokens = self.tagger.Tokenize(string)


class TimeBag(object):
    
    """A bag of strings with some attributes, resulting from the splitting of
    a Cluster (or Quote) into time windows.
    
    This object is used for analysis of the evolution of a Cluster through
    time.
    
    Methods:
      * __init__: build the TimeBag from a Cluster, a starting time, and an
                  ending time
      * levenshtein_sphere: get the strings in the TimeBag that are exactly at
                            levenshtein-distance d from a string
      * levenshtein_word_sphere: get the strings in the TimeBag that are
                                 exactly at levenshtein_word-distance d from a
                                 string
      * hamming_sphere: get the strings in the TimeBag that are exactly at
                        hamming-distance d from a string
      * hamming_word_sphere: get the strings in the TimeBag that are exactly
                             at hamming_word-distance d from a string
      * subhamming_sphere: get the strings in the TimeBag that are exactly at
                           subhamming-distance d from a string
      * subhamming_word_sphere: get the strings in the TimeBag that are
                                exactly at subhamming_word-distance d from a
                                string
      * iter_sphere_nosub: iterate through strings in timebag in a sphere
                           centered at 'base'. Yield (mother, string) tuples.
      * iter_sphere_sub: iterate through strings in timebag in a subsphere
                         centered at 'base'. Yield the (effective mother,
                         substring) tuples.
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
        
        import analyze.memetracker as a_mt
        
        framed_cluster = a_mt.frame_cluster(cluster, start, end)
        
        self.iter_sphere = {False: self.iter_sphere_nosub,
                            True: self.iter_sphere_sub}
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
    
    def qt_string_lower(self, k, parse=True):
        """Return a QtString corresponding to string number k of the Timebag,
        in lowercase."""
        return QtString(self.strings[k].lower(), self.id_fromcluster,
                        self.ids[k], parse=parse)
    
    def levenshtein_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at
        levenshtein-distance d from a string."""
        return l_mt.timebag_levenshtein_sphere(self, center_string, d)
    
    def levenshtein_word_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at
        levenshtein_word-distance d from a string."""
        return l_mt.timebag_levenshtein_word_sphere(self, center_string, d)
    
    def hamming_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at hamming-distance
        d from a string."""
        return l_mt.timebag_hamming_sphere(self, center_string, d)
    
    def hamming_word_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at
        hamming_word-distance d from a string."""
        return l_mt.timebag_hamming_word_sphere(self, center_string, d)
    
    def subhamming_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at
        subhamming-distance d from a string."""
        return l_mt.timebag_subhamming_sphere(self, center_string, d)
    
    def subhamming_word_sphere(self, center_string, d):
        """Get the strings in the TimeBag that are exactly at
        subhamming_word-distance d from a string."""
        return l_mt.timebag_subhamming_word_sphere(self, center_string, d)
    
    def iter_sphere_nosub(self, root):
        """Iterate through strings in timebag in a sphere centered at 'base'.
        Yield (mother, string) tuples."""
        return l_mt.timebag_iter_sphere_nosub(self, root)
    
    def iter_sphere_sub(self, root):
        """Iterate through strings in timebag in a subsphere centered at
        'base'. Yield the (effective mother, substring) tuples."""
        return l_mt.timebag_iter_sphere_sub(self, root)
