#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tag and tokenize sentences and quotes."""


from __future__ import division

from .treetaggerwrapper import TreeTagger, TreeTaggerError
from util.generic import find_upper_rel_dir, NotFoundError, memoize

import settings as st


class TreeTaggerTags(TreeTagger):

    """Wrapper for frequently-used functions of the TreeTagger methods.

    This is a convenience caching subclass of
    :class:`~.treetaggerwrapper.TreeTagger`. See
    :class:`~.treetaggerwrapper.TreeTagger` for initialization parameters.

    """

    def __init__(self, *args, **kwargs):
        """Initialize the structure and prepare caching of tagged strings."""
        super(TreeTaggerTags, self).__init__(*args, **kwargs)
        self._cache = {}

    def _tag_cache(self, s):
        """Tag a sentence and cache the result."""
        if s not in self._cache:
            self._cache[s] = self.TagText(s, notagdns=True)
        return self._cache[s]

    def Tags(self, s):
        """Tag a string and return the list of tags."""
        return [t.split('\t')[1] for t in self._tag_cache(s)]

    def Tokenize(self, s):
        """Tokenize a string and return the list of tokens."""
        return [t.split('\t')[0] for t in self._tag_cache(s)]

    def Lemmatize(self, s):
        """Lemmatize a string and return the list of tokens."""
        return [t.split('\t')[2] for t in self._tag_cache(s)]


def _get_tagger():
    """Get an instance of :class:`TreeTaggerTags`; but better use the singleton
    returned by :meth:`get_tagger`."""

    try:
        tagger = TreeTaggerTags(
            TAGLANG='en',
            TAGDIR=find_upper_rel_dir(st.treetagger_TAGDIR),
            TAGINENC='utf-8', TAGOUTENC='utf-8')
        return tagger
    except NotFoundError:
        raise TreeTaggerError('TreeTagger directory not found '
                              '(searched parent directories '
                              'recursively)')


get_tagger = memoize(_get_tagger)
"""Get a singleton instance of :class:`TreeTaggerTags`."""
