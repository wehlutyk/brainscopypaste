#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tag and tokenize sentences and quotes.

Classes:
  * TreeTaggerTags: wrapper for frequently-used functions of the TreeTagger
                    methods

"""


from treetaggerwrapper import TreeTagger


class TreeTaggerTags(TreeTagger):
    
    """Wrapper for frequently-used functions of the TreeTagger methods.
    
    This is a subclass of treetaggerwrapper.TreeTagger, for convenience.
    
    Methods:
      * Tags: tag a string and return the list of tags.
      * Tokenize: tokenize a string and return the list of tokens
    
    """
    
    def Tags(self, s):
        """Tag a string and return the list of tags."""
        return [t.split('\t')[1] for t in self.TagText(s)]
    
    def Tokenize(self, s):
        """Tokenize a string and return the list of tokens."""
        return self.TagText(s, prepronly=True)
