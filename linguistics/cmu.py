#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute syllable and phoneme counts based on the CMU Pronouciation data."""


from __future__ import division

from numpy import array

from nltk.corpus import cmudict

from util.generic import is_int

_prondict = cmudict.dict()


def get_all_MNphonemes():
    """Get the dict of `(word, mean number of phonemes)`."""

    return dict((w, array([len(pron) for pron in prons]).mean())
                for w, prons in _prondict.iteritems())


def count_syllables(pron):
    """Count the number of syllables in `pron`, a list of phonemes."""

    return sum([is_int(ph[-1]) for ph in pron])


def get_MNsyllables(w):
    """Get the mean number of syllables for a word `w`."""

    Nsyllabless = array([count_syllables(pron) for pron in _prondict[w]])
    return Nsyllabless.mean()


def get_all_MNsyllables():
    """Get the dict of `(word, mean number of syllables)`."""

    return dict((w, get_MNsyllables(w)) for w in _prondict.iterkeys())
