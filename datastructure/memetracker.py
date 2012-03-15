#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Structures and classes to deal with the MemeTracker dataset
'''


# Imports
from __future__ import division
from datainterface.timeparsing import isostr_to_epoch_mt
import visualize.memetracker as v_mt
# "import analyze.memetracker as a_mt" has been moved into TimeBag.__init__ to prevent a circular import problem
# see http://docs.python.org/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module for more info
from datetime import datetime
from warnings import warn
import numpy as np
import pylab as pl


# Module code
class Timeline(object):
    '''
    Holds a series of urls (with their times, etc.), and a few attributes about that series
    '''
    
    def __init__(self, length):
        self.url_times = np.zeros(length)
        self.current_idx = 0
        self.attrs_computed = False
    
    def compute_attrs(self):
        if self.current_idx != len(self.url_times):
            warn('The number of urls entered (={}) is not equal to the number '.format(self.current_idx) \
                 + 'of urls allocated for (={}) when you created this timeline object. '.format(len(self.url_times)) \
                 + 'There must be a problem somewhere')
        
        if not self.attrs_computed:
            # Start, end, and time span of the quote
            self.start = self.url_times.min()
            self.end = self.url_times.max()
            self.span = datetime.fromtimestamp(self.end) - datetime.fromtimestamp(self.start)
            self.span_days = max(1, int(round(self.span.total_seconds() / 86400)))
            
            # Histogram, and maximum instances-per-day (i.e. highest spike)
            self.ipd, bins = pl.histogram(self.url_times, self.span_days)
            self.ipd_x_secs = (bins[:-1] + bins[1:])//2
            self.argmax_ipd = np.argmax(self.ipd)
            self.max_ipd = self.ipd[self.argmax_ipd]
            self.max_ipd_x_secs = self.ipd_x_secs[self.argmax_ipd]
            
            self.attrs_computed = True
    
    def add_url(self, line_fields):
        for i in xrange(int(line_fields[3])):
            self.url_times[self.current_idx] = int(isostr_to_epoch_mt(line_fields[2]))
            self.current_idx += 1
    
    def plot(self, smooth_res=5):
        v_mt.plot_timeline(self, smooth_res=smooth_res)


class Quote(Timeline):
    def __init__(self, line_fields=None, n_urls=None, tot_freq=None, string=None, qt_id=None):
        if line_fields != None:
            if n_urls != None or tot_freq != None or string != None or qt_id != None:
                raise ValueError('Bad set of arguments when creating this quote. ' \
                                 + 'You must specify either "line_fields" (={}) '.format(line_fields) \
                                 + 'OR all of "n_urls" (={}), "tot_freq" (={}), '.format(n_urls, tot_freq) \
                                 + '"string" (={}), and "qt_id" (={}).'.format(string, qt_id))
            self.n_urls = int(line_fields[2])
            self.tot_freq = int(line_fields[1])
            self.string = line_fields[3]
            self.string_length = len(self.string)
            self.id = line_fields[4]
        else:
            if n_urls == None or tot_freq == None or string == None or qt_id == None:
                raise ValueError('Bad set of arguments when creating this quote. ' \
                                 + 'You must specify either "line_fields" (={}) '.format(line_fields) \
                                 + 'OR all of "n_urls" (={}), "tot_freq" (={}), '.format(n_urls, tot_freq) \
                                 + '"string" (={}), and "qt_id" (={}).'.format(string, qt_id))
            self.n_urls = n_urls
            self.tot_freq = tot_freq
            self.string = string
            self.string_length = len(string)
            self.id = qt_id
        
        super(Quote, self).__init__(self.tot_freq)
    
    def __repr__(self):
        return '<Quote: ' + self.__unicode__() + '>'
    
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return '"' + self.string + '" (quote #{} ; tot_freq={})'.format(self.id, self.tot_freq)
    
    def plot(self, smooth_res=5):
        v_mt.plot_timeline(self, label=self.__unicode__(), smooth_res=smooth_res)


class Cluster(object):
    def __init__(self, line_fields=None, n_quotes=None, tot_freq=None, root=None, cl_id=None):
        if line_fields != None:
            if n_quotes != None or tot_freq != None or root != None or cl_id != None:
                raise ValueError('Bad set of arguments when creating this cluster. ' \
                                 + 'You must specify either "line_fields" (={}) '.format(line_fields) \
                                 + 'OR all of "n_quotes" (={}), "tot_freq" (={}), '.format(n_quotes, tot_freq) \
                                 + '"root" (={}), and "cl_id" (={}).'.format(root, cl_id))
            self.n_quotes = int(line_fields[0])
            self.tot_freq = int(line_fields[1])
            self.root = line_fields[2]
            self.root_length = len(self.root)
            self.id = int(line_fields[3])
        else:
            if n_quotes == None or tot_freq == None or root == None or cl_id == None:
                raise ValueError('Bad set of arguments when creating this cluster. ' \
                                 + 'You must specify either "line_fields" (={}) '.format(line_fields) \
                                 + 'OR all of "n_quotes" (={}), "tot_freq" (={}), '.format(n_quotes, tot_freq) \
                                 + '"root" (={}), and "cl_id" (={}).'.format(root, cl_id))
            self.n_quotes = n_quotes
            self.tot_freq = tot_freq
            self.root = root
            self.root_length = len(root)
            self.id = cl_id
        
        self.quotes = {}
        self.timeline_built = False
    
    def __repr__(self):
        return '<Cluster: ' + self.__unicode__() + '>'
    
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return '"' + self.root + '" (cluster #{} ; tot_quotes={} ; tot_freq={})'.format(self.id, self.n_quotes, self.tot_freq)
    
    def add_quote(self, line_fields):
        self.quote[int(line_fields[4])] = Quote(line_fields)
    
    def plot_quotes(self, smooth_res=-1):
        for qt in self.quotes.values():
            qt.plot(smooth_res=smooth_res)
        pl.title(self.__unicode__())
    
    def build_timeline(self):
        if not self.timeline_built:
            self.timeline = Timeline(self.tot_freq)
            for qt in self.quotes.values():
                self.timeline.url_times[self.timeline.current_idx:self.timeline.current_idx+qt.tot_freq] = qt.url_times
                self.timeline.current_idx += qt.tot_freq
            self.timeline.compute_attrs()
            self.timeline_built = True
    
    def plot(self, smooth_res=5):
        self.build_timeline()
        v_mt.plot_timeline(self.timeline, label=self.__unicode__(), smooth_res=smooth_res)


class TimeBag(object):
    def __init__(self, cluster, start, end):
        # This import goes here to prevent a circular import problem
        import analyze.memetracker as a_mt
        framed_cluster = a_mt.frame_cluster(cluster, start, end)
        
        self.id_fromcluster = cluster.id
        self.strings = []
        self.tot_freq = framed_cluster.tot_freq
        self.tot_freqs = np.zeros(framed_cluster.n_quotes)
        self.n_urlss = np.zeros(framed_cluster.n_quotes)
        self.ids = np.zeros(framed_cluster.n_quotes)
        
        for i, qt in enumerate(framed_cluster.quotes.values()):
            self.strings.append(qt.string)
            self.tot_freqs[i] = qt.tot_freq
            self.n_urlss[i] = qt.n_urls
            self.ids[i] = qt.id
        
        self.max_freq_string = self.strings[np.argmax(self.tot_freqs)]
