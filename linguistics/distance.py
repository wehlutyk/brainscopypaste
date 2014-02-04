#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Distance tools."""


from __future__ import division

import numpy as np

from linguistics.treetagger import TaggerBuilder


def levenshtein(s1, s2):
    """Compute levenshtein distance between `s1` and `s2`."""

    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if not s2:
        return len(s1)

    previous_row = xrange(len(s2) + 1)

    for i, c1 in enumerate(s1):

        current_row = [i + 1]

        for j, c2 in enumerate(s2):

            # previous_row and current_row are one character longer than s2,
            # hence the 'j + 1'

            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def levenshtein_word(s1, s2):
    """Compute levenshtein distance between `s1` and `s2`, taking words as the
    editing unit."""

    tagger = TaggerBuilder.get_tagger()
    return levenshtein(tagger.Tokenize(s1), tagger.Tokenize(s2))


def hamming(s1, s2):
    """Compute the hamming distance between `s1` and `s2`."""

    if len(s1) != len(s2):
        return -1
    else:
        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))


def hamming_word(s1, s2):
    """Compute the hamming distance between `s1` and `s2`, taking words as the
    editing unit."""

    tagger = TaggerBuilder.get_tagger()
    return hamming(tagger.Tokenize(s1), tagger.Tokenize(s2))


def sublists(s, l):
    """Get all sublists of `s` of length `l`."""

    return [s[i:i + l] for i in range(len(s) - l + 1)]


def subhamming(s1, s2):
    """Compute the minimum hamming distance between `s2` and all sublists of
    `s1`, returning the
    `(distance, substring position in s1, substring length)` tuple."""

    l1 = len(s1)
    l2 = len(s2)

    if l1 < l2:
        return (-1, -1, -1)
    if l1 == l2:
        return (hamming(s1, s2), 0, l2)

    distances = np.zeros(l1 - l2 + 1)

    for i, subs in enumerate(sublists(s1, l2)):
        distances[i] = hamming(subs, s2)

    amin = np.argmin(distances)
    return (distances[amin], amin, l2)


def subhamming_word(s1, s2):
    """Compute the subhamming distance between `s1` and `s2`, taking words as
    the editing unit."""

    tagger = TaggerBuilder.get_tagger()
    return subhamming(tagger.Tokenize(s1), tagger.Tokenize(s2))


def distance_word_mother_nosub(base, daughter):
    """Get distance between two strings (without substrings), and return the
    `(distance, mother)` tuple."""

    return (hamming_word(base, daughter), base)


def distance_word_mother_sub(base, daughter):
    """Get distance between two strings (with substrings), and return the
    `(distance, effective mother)` tuple."""

    # This import goes here to prevent a circular import problem.

    from datastructure.full import QtString

    d, k, l = subhamming_word(base, daughter)
    mother_tok = base.tokens[k:k + l]
    mother_pos = base.POS_tags[k:k + l]
    mother = QtString(' '.join(mother_tok), base.cl_id, base.qt_id,
                      parse=False)
    mother.tokens = mother_tok
    mother.POS_tags = mother_pos
    return (d, mother)
