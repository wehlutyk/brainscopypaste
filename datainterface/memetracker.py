#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for loading data from the MemeTracker dataset

Classes:
  * MT_dataset: represent (part of) the MemeTracker dataset
  * ClustersFileParser: Abstract Base Class to help defining parser for the MemeTracker file format
  * ClustersLoader: parser for the MemeTracker file format used to load all the data into a dict of Cluster objects
"""


# Imports
from __future__ import division
import re
import os
from codecs import open as c_open
from abc import ABCMeta, abstractmethod
from datastructure.memetracker import Quote, Cluster


# Module code
class MT_dataset(object):
    
    """Represent (part of) the MemeTracker dataset.
    
    Methods:
      * __init__: initialize the class with a filename and the folder containing it
      * print_quotes_freq: create a file containing, one per line, all the quotes of the dataset and their frequencies
      * print_quote_ids: create a file containing, on each line, all the quote ids belonging to a same cluster
      * load_clusters: load the whole dataset into a dictionary of Cluster objects
    """
    
    def __init__(self, mt_filename):
        """Initialize the class with a filename and the folder containing it, for saving other files."""
        self.mt_filename = mt_filename
        self.rootfolder = os.path.split(mt_filename)[0]
    
    def print_quotes_freqs(self):
        """Create a file containing, one per line, all the quotes of the dataset and their frequencies.
        
        Effects:
          * the desired file is created in the folder containing the dataset file, named 'quotes_and_frequency'
        
        Returns: the full path to the file created.
        """
        
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
        """Create a file containing, on each line, all the quote ids belonging to a same cluster.
        
        Effects:
          * the desired file is created in the folder containing the dataset file, named 'quotes_and_frequency'
        
        Returns: the full path to the file created.
        """
        
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
        """Load the whole clusters file into a dictionary of Cluster objects.
        
        Effects:
          * the dictionary of Cluster objects is put into self.clusters
        """
        
        # Initialize the cluster file parser
        clusters_loader = ClustersLoader()
        
        # Do the parsing and save it
        print 'Loading cluster file into a dictionary of Cluster objects... ( percentage completed:',
        clusters_loader.parse(self.mt_filename)
        print ') done'
        self.clusters = clusters_loader.clusters


class ClustersFileParser:
    
    """Abstract Base Class to help defining parser for the MemeTracker file format.
    
    'Abstract Base Class' means you can't instantiate this class. It must be sub-classed, and is meant to be
    used as a building block for classes that parse the dataset file. Methods with the @abstractmethod
    decorator are not implemented here, and must be overloaded (i.e. redefined) in sub-classes. Methods starting
    with an underscore (_X) don't need to be used by sub-classes.
    
    The idea here is to ease the writing of a parser for the dataset file: a sub-class need only define the
    cluster-, quote-, and url-handlers, which define what happens when a cluster-, a quote-, or a url-declaration
    is encountered in the dataset file; the rest of the parsing code is common for all classes and is implemented
    in this base class.
    
    Methods:
      * __init__: initialize the class with some internal info for parsing and printing progress info
      * parse: parse a file, using the defined cluster-, quote-, and url-handlers
    
    Abstract methods (must be overloaded in sub-classes):
      * handle_cluster: handle a cluster definition encountered in the dataset file
      * handle_quote: handle a quote definition encountered in the dataset file
      * handle_url: handle a url definition encountered in the dataset file
    
    Private methods (don't need to be used in sub-classes)::
      * _skip_lines: skip the first few lines in an open file (usually the syntax definition lines)
      * _count_lines: count the number of lines in a file
    """
    
    # This statement makes this an Abstract Base Class. See the docstring above for what that means.
    # More details at http://docs.python.org/library/abc.html
    __metaclass__ = ABCMeta
    
    def __init__(self):
        """Initialize the class with some internal info for parsing and printing progress info."""
        # How many lines to skip at the beginning of the file
        self._n_skip = 6
        # Number of lines of the file
        self._n_lines = 8357595 # or count them directly, but it's longer: self._count_lines(mt_filename)
        # We'll print progress info each time we've read a multiple of self._lineinfostep
        self._lineinfostep = int(round(self._n_lines/20))
    
    # This decorator requires sub-classes to overload this method
    @abstractmethod
    def handle_cluster(self):
        raise NotImplementedError
    
    # This decorator requires sub-classes to overload this method
    @abstractmethod
    def handle_quote(self):
        raise NotImplementedError
    
    # This decorator requires sub-classes to overload this method
    @abstractmethod
    def handle_url(self):
        raise NotImplementedError
    
    def _skip_lines(self, f):
        """Skip the first few lines in an open file (usually the syntax definition lines).
        
        Arguments:
          * f: an open file where you want lines to be skipped
        """
        
        for i in xrange(self._n_skip):
            f.readline()
    
    def _count_lines(self, filename):
        """Count the number of lines in a file.
        
        Arguments:
          * filename: the path to the file from which the lines are counted
        
        Returns: the number of lines in the file.
        """
        
        print "Counting lines for '" + filename + "'..."
        with c_open(filename, 'rb', encoding='utf-8') as f:
            for i, l in enumerate(f):
                pass
            return i + 1
    
    def parse(self, filename):
        """Parse a file, using the defined cluster-, quote-, and url-handlers.
        
        Arguments:
          * filename: the path to the file to parse
        
        Effects: whatever effects the cluster-, quote-, and url-handlers have, and nothing else.
        """
        
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
    
    """Parser for the MemeTracker file format used to load all the data into a dict of Cluster objects.
    It is built as a sub-class of the ClustersFileParser, and therefore overloads the cluster-, quote-,
    and url-handlers. The parsing itself is implemented by the ClustersFileParser.
    
    Methods:
      * __init__: initialize the ClustersFileParser and some variables used for keeping track of what's happening during parsing
      * handle_cluster: handle a cluster definition in the dataset file
      * handle_quote: handle a quote definition in the dataset file
      * handle_url: handle a url definition in the dataset file
    """
    
    def __init__(self):
        """Initialize the ClustersFileParser and some variables used for keeping track of what's happening during parsing."""
        # Init the parent class
        super(ClustersLoader, self).__init__()
        
        # Variables keeping track of what cluster and what quote we're currently parsing
        self.cluster_id = None
        self.quote_id = None
        # Init the result: a dict of Cluster objects
        self.clusters = {}
    
    def handle_cluster(self, line_fields):
        """Handle a cluster definition in the dataset file."""
        # Remember the Cluster id
        self.cluster_id = int(line_fields[3])
        # And create the Cluster in the root dict
        self.clusters[self.cluster_id] = Cluster(line_fields)
    
    def handle_quote(self, line_fields):
        """Handle a quote definition in the dataset file."""
        # Remember the Quote id
        self.quote_id = int(line_fields[4])
        # And create the Quote in the current Cluster's sub-dict
        self.clusters[self.cluster_id].quotes[self.quote_id] = Quote(line_fields)
    
    def handle_url(self, line_fields):
        """Handle a url definition in the dataset file."""
        # Add that url the current Quote's Timeline
        self.clusters[self.cluster_id].quotes[self.quote_id].add_url(line_fields)
