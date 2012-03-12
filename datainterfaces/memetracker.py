#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Structures and methods to deal with the MemeTracker dataset
See http://memetracker.org/ for details about it
'''


# Imports
from __future__ import division
from codecs import open as c_open
from abc import ABCMeta, abstractmethod
from datainterfaces.timeparsing import isostr_to_epoch_mt
from datetime import datetime
import numpy as np
import pylab as pl
import re
import os


# Module code
class MT_dataset(object):
    def __init__(self, mt_filename):
        self.mt_filename = mt_filename
        self.rootfolder = os.path.split(mt_filename)[0]
    
    def print_quotes_freq(self):
        '''
        Reads the clusters file and prints out in another file what quotes are present, along with their frequencies
        '''
        
        # Open the files
        outfilename = os.path.join(self.rootfolder, 'quotes_and_frequency')
        with c_open(self.mt_filename, 'rb', encoding='utf-8') as infile, \
             c_open(outfilename, 'wb', encoding='utf-8') as outfile:
            # Skip the first lines
            self.skip_lines(infile)
            
            # Parse it all
            print 'Reading cluster file and writing the quotes and frequencies...',
            for line in infile:
                if line[0] == '\t' and line[1] != '\t':
                    tokens = line.split('\t')
                    outfile.write(u'%s\t%d\n' % (tokens[3], int(tokens[1])))
            print 'done'
        
        # Return the created file name
        return outfilename

    def print_quote_ids(self):
        '''
        Reads the cluster file and prints out on each line all the quotes that belong to the same cluster
        (Was called 'leskovec_clusters_encoding.py', changed to this name to reflect what is does)
        '''
        
        # Open the files
        outfilename = os.path.join(self.rootfolder, 'quote_ids')
        with c_open(self.mt_filename, 'rb', encoding='utf-8') as infile, \
             c_open(outfilename, 'wb', encoding='utf-8') as outfile:
            # Skip the first few lines
            self.skip_lines(infile)
            
            # Parse it all
            print 'Reading cluster file and writing quote ids...',
            clust = []
            j = 0
            for line in infile:
                line0 = re.split(r'[\xa0\s+\t\n]+', line)
                if line0[0] != '':
                    clust.append([])
                elif line[0] == '\t' and line[1] != '\t':
                    clust[-1].append(j)
                    j += 1
            
            for cl in clust:
                for x in cl:
                    outfile.write('%d ' % x)
                outfile.write('\n')
            
            print 'done'
        
        # Return the created file name
        return outfilename
    
    def load_clusters(self):
        '''
        Load the whole clusters file into a dictionary
        '''
        
        # Initialize the cluster file parser
        clusters_loader = ClustersLoader()
        
        # Do the parsing and save it
        print 'Loading cluster file into a dictionary... ( percentage completed:',
        clusters_loader.parse(self.mt_filename)
        print ') done'
        self.clusters = clusters_loader.clusters
    
    def load_clusters_timeline(self):
        '''
        Load quote times for each cluster, and put that into a dictionary
        '''
        
        # Initialize the cluster file parser
        clusters_timeline_loader = ClustersTimelineLoader()
        
        # Do the parsing and save it
        print 'Loading the times of urls, for each cluster, into a dictionary... ( percentage completed:',
        clusters_timeline_loader.parse(self.mt_filename)
        print ') done'
        self.clusters_timeline = clusters_timeline_loader.clusters_timeline
    
    def load_clustersquotes_timeline(self):
        '''
        Load quote times for each quote for each cluster, and put that into nested dictionaries
        '''
        
        # Initialize the cluster file parser
        clustersquotes_timeline_loader = ClustersQuotesTimelineLoader()
        
        # Do the parsing and save it
        print 'Loading the times of urls, for each quote, for each cluster, into a dictionary... ( percentage completed:',
        clustersquotes_timeline_loader.parse(self.mt_filename)
        print ') done'
        self.clustersquotes_timeline = clustersquotes_timeline_loader.clustersquotes_timeline


class ClustersFileParser:
    '''
    An abstract class to define cluster file parsers, with custom cluster-, quote-, and url-handlers
    '''
    
    # Make this an abstract base class: can't be instantiated, must be sub-classed
    # In addition, methods marked @abstractmethod must be overridden
    # (i.e. they're not implemented here, but should be implemented in sub-classes)
    __metaclass__ = ABCMeta
    
    def __init__(self):
        # Some variables to print progress info
        self._n_skip = 6
        self._n_lines = 8357595 # or count them self._count_lines(mt_filename)
        self._lineinfostep = int(round(self._n_lines/20))
    
    @abstractmethod
    def handle_cluster(self):
        raise NotImplementedError
    
    @abstractmethod
    def handle_quote(self):
        raise NotImplementedError
    
    @abstractmethod
    def handle_url(self):
        raise NotImplementedError
    
    def _skip_lines(self, f):
        '''
        Skip the first few lines in a file object
        '''
        
        for i in xrange(self._n_skip):
            f.readline()
    
    def _count_lines(self, filename):
        '''
        Count the lines of a file
        '''
        
        print "Counting lines for '" + filename + "'..."
        with c_open(filename, 'rb', encoding='utf-8') as f:
            for i, l in enumerate(f):
                pass
            return i + 1
    
    def parse(self, filename):
        '''
        Do the actual parsing
        '''
        
        # Open the file
        with c_open(filename, 'rb', encoding='utf-8') as infile:
            # Skip the first few lines
            self._skip_lines(infile)
            
            # Parse the file
            for i, line in enumerate(infile):
                # Give some info about progress
                if i % self._lineinfostep == 0:
                    print int(round(i*100/self._n_lines)),
                line0 = re.split(r'[\xa0\s+\t\r\n]+', line)
                line_fields = re.split(r'[\t\r\n]', line)
                # Is this a cluster definition line?
                if line0[0] != '':
                    self.handle_cluster(line_fields)
                # Is this a quote definition line?
                elif line[0] == '\t' and line[1] != '\t':
                    self.handle_quote(line_fields)
                # Is this a url definition line?
                elif line[0] == '\t' and line[1] == '\t' and line[2] != '\t':
                    self.handle_url(line_fields)


class ClustersLoader(ClustersFileParser):
    '''
    A class to parse a cluster file, and load it all into a dictionary
    '''
    
    def __init__(self):
        # Init the parent class
        super(ClustersLoader, self).__init__()
        
        # Init the counters and the result
        self.cluster_id = None
        self.quote_id = None
        self.clusters = {}
    
    def handle_cluster(self, line_fields):
        # Set the cluster id
        self.cluster_id = int(line_fields[3])
        
        # And create the cluster in the root dictionary
        self.clusters[self.cluster_id] = {'ClSz': int(line_fields[0]), \
                                   'TotFq': int(line_fields[1]), \
                                   'Root': line_fields[2], \
                                   'Quotes': {}}
    
    def handle_quote(self, line_fields):
        # Set the quote id
        self.quote_id = int(line_fields[4])
        
        # Create the quote in the current cluster's sub-dictionary
        self.clusters[self.cluster_id]['Quotes'][self.quote_id] = {'QtFq': int(line_fields[1]), \
                                                                   'N_Urls': int(line_fields[2]), \
                                                                   'QtStr': line_fields[3], \
                                                                   'Links': {}}
    
    def handle_url(self, line_fields):
        # Add that url the the current quote's sub-dictionary
        self.clusters[self.cluster_id]['Quotes'][self.quote_id]['Links'][line_fields[5]] = {'Tm': line_fields[2], \
                                                                                            'Fq': int(line_fields[3]), \
                                                                                            'UrlTy': line_fields[4]}


class ClustersTimelineLoader(ClustersFileParser):
    '''
    A class to load, from the cluster file, the time of all the urls belonging to a cluster ;
    and that for each cluster. This results in a dictionary of numpy arrays: each dictionary
    key is a cluster id, and the corresponding array is the list of times at which the urls
    (belonging to that cluster) were published (there is *NO* per-quote-distinction).
    '''
    
    def __init__(self):
        # Init the parent class
        super(ClustersTimelineLoader, self).__init__()
        
        # Init the counters and the result
        self.cluster_id = None
        self.url_cnt = None
        self.clusters_timeline = {}
    
    def handle_cluster(self, line_fields):
        # Set the quote counter and the cluster id
        self.cluster_id = int(line_fields[3])
        self.url_cnt = 0
        
        # Create an array of TotFq size in the root dictionary, to save the url times later on
        self.clusters_timeline[self.cluster_id] = np.zeros(int(line_fields[1]))
    
    def handle_quote(self, line_fields):
        # Nothing to do!
        pass
    
    def handle_url(self, line_fields):
        # Add the url time to the current array in the root dictionary
        # Add one instance for each time the quote appeared in that post
        for i in xrange(int(line_fields[3])):
            self.clusters_timeline[self.cluster_id][self.url_cnt] = isostr_to_epoch_mt(line_fields[2])
            self.url_cnt += 1


class ClustersQuotesTimelineLoader(ClustersFileParser):
    '''
    A class to load, from the cluster file, the time of all the urls belonging to a quote, belonging to cluster ;
    and that for each cluster. This results in a dictionary (keys=clusters) of dictionaries (keys=quotes) of
    dictionaries (keys=quote properties and a numpy array corresponding to the time of each url)
    (here, a distinction is made between the quotes)
    '''
    
    def __init__(self):
        # Init the parent class
        super(ClustersQuotesTimelineLoader, self).__init__()
        
        # Init the counters and the result
        self.cluster_id = None
        self.quote_id = None
        self.url_cnt = None
        self.clustersquotes_timeline = {}
    
    def handle_cluster(self, line_fields):
        # Set the cluster id
        self.cluster_id = int(line_fields[3])
        
        # Create a sub-dictionary for the cluster
        self.clustersquotes_timeline[self.cluster_id] = {'Root': line_fields[2], 'Quotes': {}}
    
    def handle_quote(self, line_fields):
        # Set the quote id and the url counter
        self.quote_id = int(line_fields[4])
        self.url_cnt = 0
        
        # Create a dictionary with relevant data
        self.clustersquotes_timeline[self.cluster_id]['Quotes'][self.quote_id] = {'QtStr': line_fields[3], \
                                                                                  'Times': np.zeros(int(line_fields[1]))}
    
    def handle_url(self, line_fields):
        # Add the url time to the current array in the root dictionary
        # Add one instance for each time the quote appeared in that post
        for i in xrange(int(line_fields[3])):
            self.clustersquotes_timeline[self.cluster_id]['Quotes'][self.quote_id]['Times'][self.url_cnt] = isostr_to_epoch_mt(line_fields[2])
            self.url_cnt += 1


class Quote(object):
    '''
    Holds a quote and a few attributes about it
    '''
    
    def __init__(self, line_fields):
        self.tot_freq = int(line_fields[1])
        self.tot_urls = int(line_fields[2])
        self.string = line_fields[3]
        self.id = line_fields[4]
        self.urls = []
        self.url_times = []
        self.url_freqs = []
        self.url_types = []
        self.attrs_computed = False
    
    def compute_attrs(self):
        if self.attrs_computed:
            raise Exception('Attributes already computed for quote {} (string "{}")'.format(self.id, self.string))
        
        if len(self.url_times) > 0:
            # Start, end, and time span of the quote
            self.start = datetime.fromtimestamp(np.amin(self.url_times))
            self.end = datetime.fromtimestamp(np.amax(self.url_times))
            self.span = self.end - self.start
            self.span_days = int(round(self.span.total_seconds() / 86400))
            
            # Maximum instances-per-day (i.e. highest spike)
            self.ipd, bins = pl.histogram(self.url_times, self.span_days)
            self.ipd_x_secs = (bins[:-1] + bins[1:])//2
            self.argmax_ipd = np.argmax(self.ipd)
            self.max_ipd = self.ipd[self.argmax_ipd]
            self.max_ipd_x_secs = self.ipd_x_secs[self.argmax_ipd]
            
            self.attrs_computed = True