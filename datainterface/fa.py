#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load data from raw files from the University of South Florida Free
Association Norms.

Classes:
  * FreeAssociationNorms: load raw Free Association norms files (Appendix A
                          from http://w3.usf.edu/FreeAssociation/) and parse
                          them

"""


from codecs import open as c_open


class FreeAssociationNorms(object):

    """Load raw Free Association norms files (Appendix A from
    http://w3.usf.edu/FreeAssociation/) and parse them.

    Methods:
      * __init__: initialize the filenames the be parsed
      * _skip_lines: skip the first few lines in an open file (usually the
                     syntax definition lines)
      * load_norms: parse the Appendix A files and save results in self.norms

    """

    def __init__(self, filenames):
        """Initialize the filenames the be parsed."""
        self.filenames = filenames
        self._n_skip = 4

    def _skip_lines(self, f):
        """Skip the first few lines in an open file (usually the syntax
        definition lines).

        Arguments:
          * f: an open file where you want lines to be skipped

        """

        for i in xrange(self._n_skip):
            f.readline()

    def load_norms(self):
        """Parse the Appendix A files and save results in self.norms.

        Effects: set self.norms to a dict containing, for each (lowercased)
                 cue, a list of tuples. Each tuple represents a word
                 referenced by the cue, and is in format (word, ref, weight):
                 'word' is the word referenced; 'ref' is a boolean indicating
                 if 'word' has been normed or not; 'weight' is the strength of
                 the referencing.

        """

        self.norms = {}

        for filename in self.filenames:

            with c_open(filename, 'rb') as f:

                self._skip_lines(f)

                for line in f:

                    # Exit if we're at the end of the data.

                    if line[0] == '<':
                        break

                    # Parse our line.

                    linefields = line.split(', ')
                    w1 = linefields[0].lower()
                    w2 = linefields[1].lower()

                    if linefields[2].lower() == 'yes':
                        ref = True
                    else:
                        ref = False

                    weight = float(linefields[5])

                    newitem = (w2, ref, weight)

                    try:
                        self.norms[w1].append(newitem)
                    except KeyError:
                        self.norms[w1] = [newitem]
