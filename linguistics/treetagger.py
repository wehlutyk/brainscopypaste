#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tag and tokenize sentences and quotes.

Variables:
  * tagger: an initialized instance of TreeTaggerTags

Classes:
  * TreeTaggerTags: wrapper for frequently-used functions of the TreeTagger
                    methods

"""


from __future__ import division

from .treetaggerwrapper import TreeTagger, TreeTaggerError
from util.generic import find_upper_rel_dir, NotFoundError

import settings as st


class TreeTaggerTags(TreeTagger):

    """Wrapper for frequently-used functions of the TreeTagger methods.

    This is a subclass of treetaggerwrapper.TreeTagger, for convenience.

    Methods:
      * __init__: prepare caching of tagged strings
      * _tag_cache: tag a sentence and cache the result
      * Tags: tag a string and return the list of tags.
      * Tokenize: tokenize a string and return the list of tokens
      * Lemmatize: lemmatize a string a return the list of tokens

    """

    def __init__(self, *args, **kwargs):
        """Prepare caching of tagged strings."""
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



class TaggerBuilder(object):

    tagger = None

    @classmethod
    def get_tagger(cls):
        if not cls.tagger:
            try:
                cls.tagger = TreeTaggerTags(
                        TAGLANG='en',
                        TAGDIR=find_upper_rel_dir(st.treetagger_TAGDIR),
                        TAGINENC='utf-8', TAGOUTENC='utf-8')
            except NotFoundError:
                raise TreeTaggerError('TreeTagger directory not found '
                                      '(searched parent directories '
                                      'recursively)')
        return cls.tagger
