#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load data from the MemeTracker dataset."""


from __future__ import division

import re
import os
from codecs import open as c_open
from abc import ABCMeta, abstractmethod

from datastructure.full import Quote, Cluster


class MT_dataset(object):

    """Represent (part of) the MemeTracker dataset.

    Parameters
    ----------
    mt_filename : string
        Path to the MemeTracker dataset file.

    Attributes
    ----------
    clusters : dict of :class:`~datastructure.full.Cluster`\ s
        Created when calling :meth:`load_clusters`.

    Methods
    -------
    load_clusters()
        Load the whole dataset into a dictionary of \
                :class:`~datastructure.full.Cluster` objects.

    """

    def __init__(self, mt_filename):
        """Initialize the instance with the filename of the MemeTracker
        dataset.

        Parameters
        ----------
        mt_filename : string
            Path to the MemeTracker dataset file.

        """

        self.mt_filename = mt_filename
        self.rootfolder = os.path.split(mt_filename)[0]

    def load_clusters(self):
        """Load the whole dataset into a dictionary of
        :class:`~datastructure.full.Cluster` objects.

        The dictionary of Cluster objects is stored in ``self.clusters``.

        See Also
        --------
        ClustersLoader

        """

        # Initialize the cluster file parser.

        clusters_loader = ClustersLoader()

        # Do the parsing and save it.

        print ('Loading cluster file into a dictionary of Cluster '
               'objects... ( percentage completed:'),

        clusters_loader.parse(self.mt_filename)
        self.clusters = clusters_loader.clusters

        print ') done'


class ClustersFileParser(object):

    """Abstract Base Class to help defining parser for the MemeTracker file
    format.

    'Abstract Base Class' means you can't instantiate this class. It must be
    subclassed, and is meant to be used as a building block for classes that
    parse the dataset file. Methods with the @abstractmethod decorator are not
    implemented here, and must be overloaded (i.e. redefined) in subclasses.
    Methods starting with an underscore (_X) don't need to be used by
    subclasses.

    The idea here is to ease the writing of a parser for the dataset file: a
    subclass need only define the cluster-, quote-, and url-handlers, which
    define what happens when a cluster-, a quote-, or a url-declaration is
    encountered in the dataset file; the rest of the parsing code is common
    for all classes and is implemented in this base class.

    Methods:
      * __init__: initialize the class with some internal info for parsing and
                  printing progress info
      * parse: parse a file, using the defined cluster-, quote-, and
               url-handlers

    Abstract methods (must be overloaded in subclasses):
      * handle_cluster: handle a cluster definition encountered in the dataset
                        file
      * handle_quote: handle a quote definition encountered in the dataset
                      file
      * handle_url: handle a url definition encountered in the dataset file

    Private methods (don't need to be used in subclasses)::
      * _skip_lines: skip the first few lines in an open file (usually the
                     syntax definition lines)
      * _count_lines: count the number of lines in a file

    """

    # This statement makes this an Abstract Base Class. See the docstring
    # above for what that means. More details at
    # http://docs.python.org/library/abc.html.

    __metaclass__ = ABCMeta

    def __init__(self):
        """Initialize the class with some internal info for parsing and
        printing progress info."""

        # How many lines to skip at the beginning of the file.

        self._n_skip = 6

        # Number of lines of the file

        self._n_lines = 8357595

        # or count them directly, but it's longer:
        # self._count_lines(mt_filename)

        # We'll print progress info each time we've read a multiple of
        # 'self._lineinfostep'.

        self._lineinfostep = int(round(self._n_lines / 20))

    # This decorator requires subclasses to overload this method.

    @abstractmethod
    def handle_cluster(self):
        raise NotImplementedError

    # This decorator requires subclasses to overload this method.

    @abstractmethod
    def handle_quote(self):
        raise NotImplementedError

    # This decorator requires subclasses to overload this method.
    @abstractmethod
    def handle_url(self):
        raise NotImplementedError

    def _skip_lines(self, f):
        """Skip the first few lines in an open file (usually the syntax
        definition lines).

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

        Effects: whatever effects the cluster-, quote-, and url-handlers have,
                 and nothing else.

        """

        with c_open(filename, 'rb', encoding='utf-8') as infile:

            # The first lines are not data.

            self._skip_lines(infile)

            # Parse the file.

            for i, line in enumerate(infile):

                # Give some info about progress

                if i % self._lineinfostep == 0:
                    print int(round(i*100/self._n_lines)),

                line0 = re.split(r'[\xa0\s+\t\r\n]+', line)
                line_fields = re.split(r'[\t\r\n]', line)

                if line0[0] != '':

                    # This is a cluster definition line.

                    self.handle_cluster(line_fields)

                elif line[0] == '\t' and line[1] != '\t':

                    # This is a quote definition line.

                    self.handle_quote(line_fields)

                elif line[0] == '\t' and line[1] == '\t' and line[2] != '\t':
                    # This is a url definition line.

                    self.handle_url(line_fields)


class ClustersLoader(ClustersFileParser):

    """Parse the MemeTracker file format to load all the data into a dict of
    Cluster objects.

    This is built as a subclass of the ClustersFileParser, and therefore
    overloads the cluster-, quote-, and url-handlers. The parsing itself is
    implemented by the ClustersFileParser.

    Methods:
      * __init__: initialize the ClustersFileParser and some variables used
                  for keeping track of what's happening during parsing
      * handle_cluster: handle a cluster definition in the dataset file
      * handle_quote: handle a quote definition in the dataset file
      * handle_url: handle a url definition in the dataset file

    """

    def __init__(self):
        """Initialize the ClustersFileParser and some variables used for
        keeping track of what's happening during parsing."""

        # Init the parent class.

        super(ClustersLoader, self).__init__()

        # Variables keeping track of what cluster and what quote we're
        # currently parsing.

        self.cluster_id = None
        self.quote_id = None

        # Init the result: a dict of Cluster objects.

        self.clusters = {}

    def handle_cluster(self, line_fields):
        """Handle a cluster definition in the dataset file."""

        # Remember the Cluster id.

        self.cluster_id = int(line_fields[3])

        # And create the Cluster in the root dict.

        self.clusters[self.cluster_id] = Cluster(line_fields)

    def handle_quote(self, line_fields):
        """Handle a quote definition in the dataset file."""

        # Remember the Quote id.

        self.quote_id = int(line_fields[4])

        # And create the Quote in the current Cluster's sub-dict.

        self.clusters[self.cluster_id].quotes[self.quote_id] = \
            Quote(line_fields)

    def handle_url(self, line_fields):
        """Handle a url definition in the dataset file."""

        # Add that url the current Quote's Timeline.

        self.clusters[self.cluster_id].quotes[self.quote_id].\
            add_url(line_fields)
