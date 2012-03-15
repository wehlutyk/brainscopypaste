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
from datastructure.memetracker import Quote, Cluster
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
        Load the whole clusters file into a dictionary of Cluster objects
        '''
        
        # Initialize the cluster file parser
        clusters_loader = ClustersLoader()
        
        # Do the parsing and save it
        print 'Loading cluster file into a dictionary of Cluster objects... ( percentage completed:',
        clusters_loader.parse(self.mt_filename)
        print ') done'
        self.clusters = clusters_loader.clusters


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
        # Remember the cluster id
        self.cluster_id = int(line_fields[3])
        # And create the cluster in the root dictionary
        self.clusters[self.cluster_id] = Cluster(line_fields)
    
    def handle_quote(self, line_fields):
        # Remember the quote id
        self.quote_id = int(line_fields[4])
        # And create the quote in the current cluster's sub-dictionary
        self.clusters[self.cluster_id].quotes[self.quote_id] = Quote(line_fields)
    
    def handle_url(self, line_fields):
        # Add that url the the current quote's timeline
        self.clusters[self.cluster_id].quotes[self.quote_id].add_url(line_fields)
