#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute syllable and phoneme counts based on the CMU Pronouciation data.

Methods:
* get_all_MNphonemes: get the dict of (word, mean number of phonemes)
* is_int: test if a string represents an integer
* count_syllables: count the number of syllables in a list of phonemes
* get_MNsyllables: get the mean number of syllables for a word
* get_all_MNsyllables: get the dict of (word, mean number of syllables)

Variables:
* prondict: the CMU pronounciation dict. Used internally.

"""


from __future__ import division

from numpy import array

from nltk.corpus import cmudict

from util.generic import is_int

prondict = cmudict.dict()


def get_all_MNphonemes():
    """Get the dict of (word, mean number of phonemes)."""
    return dict((w, array([len(pron) for pron in prons]).mean())
                for w, prons in prondict.iteritems())


def count_syllables(pron):
    """Count the number of syllables in a list of phonemes."""
    return sum([is_int(ph[-1]) for ph in pron])


def get_MNsyllables(w):
    """Get the mean number of syllables for a word."""
    Nsyllabless = array([count_syllables(pron) for pron in prondict[w]])
    return Nsyllabless.mean()


def get_all_MNsyllables():
    """Get the dict of (word, mean number of syllables)."""
    return dict((w, get_MNsyllables(w)) for w in prondict.iterkeys())
