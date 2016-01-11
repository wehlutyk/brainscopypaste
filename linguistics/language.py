#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Detect stopwords.

"""


from util.generic import memoize
import settings as st


class StopwordsDetector(object):

    """Detect if a word is a stopword."""

    def __init__(self):
        """Read and load stopwords file."""

        self.stopwords_file = st.stopwords_file
        self.stopwords = set([])
        with open(self.stopwords_file) as f:
            for l in f:
                self.stopwords.add(l.strip().lower())

    def __call__(self, word):
        """Is `word` a stopword or not."""

        return word in self.stopwords


def _get_stopdetector():
    """Get an instance of :class:`StopwordsDetector`; but better use the singleton
    returned by :meth:`get_stopdetector`."""

    return StopwordsDetector()


get_stopdetector = memoize(_get_stopdetector)
"""Get a singleton instance of :class:`StopwordsDetector`."""
