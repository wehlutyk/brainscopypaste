#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load data from raw files from the University of South Florida Free
Association Norms."""


from __future__ import division

from codecs import open as c_open


class FreeAssociationNorms(object):

    """Load raw Free Association norms files (Appendix A from
    http://w3.usf.edu/FreeAssociation/) and parse them.

    Use this class by creating an instance and then calling its
    :meth:`load_norms` method.

    Parameters
    ----------
    filenames : list of strings
        The list of paths to the files constituting the Free Association Norms.

    Attributes
    ----------
    norms : dict
        Mapping of ``word, norms`` couples (words in lowercase). Created by \
                :meth:`load_norms`.

    Methods
    -------
    _skip_lines()
        Skip the first few lines in an open file (usually the syntax \
                definition lines).
    load_norms()
        Parse the Appendix A files.

    """

    def __init__(self, filenames):
        """Initialize the filenames to be parsed."""

        self.filenames = filenames
        self._n_skip = 4

    def _skip_lines(self, f):
        """Skip the first few lines in an open file (usually the syntax
        definition lines).

        Parameters
        ----------
        f : file descriptor
            The open file in which you want lines to be skipped.

        """

        for i in xrange(self._n_skip):
            f.readline()

    def load_norms(self):
        """Parse the Appendix A files.

        After loading, ``self.norms`` is a dict containing, for each
        (lowercased) cue, a list of tuples. Each tuple represents a word
        referenced by the cue, and is in format ``(word, ref, weight)``:
        ``word`` is the referenced word; ``ref`` is a boolean indicating
        if ``word`` has been normed or not; ``weight`` is the strength of
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
