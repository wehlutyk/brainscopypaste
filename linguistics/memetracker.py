#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Linguistic analysis tools for the MemeTracker dataset.

Methods:
  * levenshtein: compute levenshtein distance between s1 and s2
  * levenshtein_word: compute levenshtein distance between s1 and s2, taking
                      words as the editing unit
  * timebag_levenshtein_sphere: get the indexes of the strings in a TimeBag
                                that are at levenshtein-distance == d from a
                                string
  * timebag_levenshtein_word_sphere: get the indexes of the strings in a
                                     TimeBag that are at
                                     levenshtein_word-distance == d from a
                                     string
  * hamming: compute hamming distance between s1 and s2
  * hamming_word: compute hamming distance between s1 and s2, taking words as
                  the editing unit
  * timebag_hamming_sphere: get the indexes of the strings in a TimeBag that
                            are at hamming-distance == d from a string
  * timebag_hamming_word_sphere: get the indexes of the strings in a TimeBag
                                 that are at hamming_word-distance == d from a
                                 string
  * sublists: get all sublists of s of length l
  * subhamming: compute the minimum hamming distance between s2 and all
                sublists of s1
  * subhamming_word: compute subhamming distance between s1 and s2, taking
                     words as the editing unit
  * timebag_subhamming_sphere: get the indices and motherstrings of the
                               substrings in a TimeBag that are at
                               subhamming-distance == d from a string
  * timebag_subhamming_word_sphere: get the indices and motherstrings of the
                                    substrings in a TimeBag that are at
                                    subhamming_word-distance == d from a
                                    string
  * timebag_iter_sphere_nosub: iterate through strings in timebag in a sphere
                               centered at 'root'. Yield the (mother,
                               substring) tuples.
  * timebag_iter_sphere_sub: iterate through strings in timebag in a subsphere
                             centered at 'root'. Yield the (effective mother,
                             substring) tuples.
  * cluster_iter_substitutions_root: iterate through substitutions taken as
                                     changes from root string. Yield (mother,
                                     substring) tuples.
  * cluster_iter_substitutions_tbgs: iterate through substitutions taken as
                                     changes between timebags. Yield (mother,
                                     substring) tuples.
  * cluster_iter_substitutions_cumtbgs: iterate through substitutions taken as
                                        changes between cumulated timebags.
                                        Yield (mother, substring) tuples.
  * distance_word_mother_nosub: get distance between two strings (without
                                substrings), and return the (distance, mother)
                                tuple
  * distance_word_mother_sub: get distance between two strings (with
                              substrings), and return the (distance, effective
                              mother) tuple
  * cluster_iter_substitutions_time: iterate through substitutions taken as
                                     transitions from earlier quotes to older
                                     quotes (in order of appearance in time)

"""


from datetime import datetime

import numpy as np

from analyze.combinatorials import build_ordered_tuples
from linguistics.distance import (levenshtein, levenshtein_word, hamming,
                                  hamming_word, subhamming, subhamming_word,
                                  distance_word_mother_nosub,
                                  distance_word_mother_sub)
from linguistics.treetagger import tagger
import datastructure.memetracker_base as ds_mtb


class TimeBagLinguistics(ds_mtb.TimeBagBase):

    def __init__(self, *args, **kwargs):
        super(TimeBagLinguistics, self).__init__(*args, **kwargs)
        self.iter_sphere = {False: self.iter_sphere_nosub,
                            True: self.iter_sphere_sub}
        self.has_mother = {False: self.has_mother_nosub,
                           True: self.has_mother_sub}

    def qt_string_lower(self, k, parse=True):
        """Return a QtString corresponding to string number k of the Timebag,
        in lowercase."""
        from datastructure.memetracker import QtString
        return QtString(self.strings[k].lower(), self.id_fromcluster,
                        self.ids[k], parse=parse)

    def levenshtein_sphere(self, center_string, d):
        """Get the indexes of the strings in a TimeBag that are at
        levenshtein-distance == d from a string."""
        distances = np.array([levenshtein(center_string, bag_string)
                            for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def levenshtein_word_sphere(self, center_string, d):
        """Get the indexes of the strings in a TimeBag that are at
        levenshtein_word-distance == d from a string."""
        distances = np.array([levenshtein_word(center_string, bag_string)
                            for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def hamming_sphere(self, center_string, d):
        """Get the indexes of the strings in a TimeBag that are at
        hamming-distance == d from a string."""
        distances = np.array([hamming(center_string, bag_string)
                            for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def hamming_word_sphere(self, center_string, d):
        """Get the indexes of the strings in a TimeBag that are at
        hamming_word-distance == d from a string."""
        distances = np.array([hamming_word(center_string, bag_string)
                            for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def subhamming_sphere(self, center_string, d):
        """Get the indices and motherstrings of the substrings in a TimeBag that
        are at subhamming-distance == d from a string."""
        subhs = [subhamming(center_string, bag_string)
                for bag_string in self.strings]
        distances = np.array([subh[0] for subh in subhs])
        subindices = np.array([subh[1] for subh in subhs])
        lens = np.array([subh[2] for subh in subhs])

        idx = np.where(distances == d)

        if len(idx) > 0:

            motherstrings = [(subindices[i], lens[i]) for i in idx[0]]
            return zip(idx[0].tolist(), motherstrings)

        else:
            return []

    def subhamming_word_sphere(self, center_string, d):
        """Get the indices and motherstrings of the substrings in a TimeBag that
        are at subhamming_word-distance == d from a string."""
        subhs = [subhamming_word(center_string, bag_string)
                for bag_string in self.strings]
        distances = np.array([subh[0] for subh in subhs])
        subindices = np.array([subh[1] for subh in subhs])
        lens = np.array([subh[2] for subh in subhs])

        idx = np.where(distances == d)

        if len(idx) > 0:

            motherstrings = [(subindices[i], lens[i]) for i in idx[0]]
            return zip(idx[0].tolist(), motherstrings)

        else:
            return []

    def has_mother_nosub(self, dest):
        """Test if this timebag's max freq string is a nosub mother for dest.
        If so, yield a (mother, daughter) tuple. Else return."""
        base = self.qt_string_lower(self.argmax_freq_string)
        if hamming_word(base, dest) == 1:
            yield (base, dest)

    def has_mother_sub(self, dest):
        """Test if this timebag's max freq string is a sub mother for dest.
        If so, yield an (effective mother, daughter) tuple. Else return."""

        import datastructure.memetracker as ds_mt

        base = self.qt_string_lower(self.argmax_freq_string)
        (d, idx, l) = subhamming_word(base, dest)
        if d == 1:
            mother_tok = base.tokens[idx:idx + l]
            mother_pos = base.POS_tags[idx:idx + l]
            mother = ds_mt.QtString(' '.join(mother_tok), base.cl_id,
                                    base.qt_id, parse=False)
            mother.tokens = mother_tok
            mother.POS_tags = mother_pos
            yield (mother, dest)

    def iter_sphere_nosub(self, base):
        """Iterate through strings in timebag in a sphere centered at 'base'.
        Yield (mother, string) tuples."""
        for k in self.hamming_word_sphere(base, 1):
            yield (base, self.qt_string_lower(k))

    def iter_sphere_sub(self, base):
        """Iterate through strings in timebag in a subsphere centered at
        'base'. Yield the (effective mother, substring) tuples."""

        # This import goes here to prevent a circular import problem.

        from datastructure.memetracker import QtString

        for k, m in self.subhamming_word_sphere(base, 1):

            mother_tok = base.tokens[m[0]:m[0] + m[1]]
            mother_pos = base.POS_tags[m[0]:m[0] + m[1]]
            mother = QtString(' '.join(mother_tok), base.cl_id, base.qt_id,
                            parse=False)
            mother.tokens = mother_tok
            mother.POS_tags = mother_pos
            yield (mother, self.qt_string_lower(k))


class QuoteLinguistics(ds_mtb.QuoteBase):

        def to_qt_string_lower(self, cl_id, parse=True):
            """Return a QtString built from this Quote, in lowercase."""
            from datastructure.memetracker import QtString
            return QtString(self.string.lower(), cl_id, self.id, parse=parse)


class ClusterLinguistics(ds_mtb.ClusterBase):

    def __init__(self, *args, **kwargs):
        super(ClusterLinguistics, self).__init__(*args, **kwargs)

    @property
    def iter_substitutions(self):
        return ds_mtb.dictionarize_attributes(self, 'iter_substitutions_')

    def iter_substitutions_root(self, argset):
        """Iterate through substitutions taken as changes from root string. Yield
        (mother, string or substring, bag info) tuples."""

        # This import goes here to prevent a circular import problem.

        from datastructure.memetracker import QtString

        base = QtString(self.root.lower(), self.id, 0)
        tbgs = self.build_timebags(argset['n_timebags'])

        for j in range(0, argset['n_timebags']):

            for mother, daughter in tbgs[j].iter_sphere[
                                        argset['substrings']](base):
                yield (mother, daughter, {'tobag': j})

    def iter_substitutions_slidetbgs(self, argset):
        """Iterate through substitutions taken as changes from the preceding
        time window. Yield (mother, string or substring, None) tuples."""

        for qt2 in self.quotes.itervalues():
            dest = qt2.to_qt_string_lower(self.id)
            prevtbg = self.build_timebag(argset['n_timebags'], qt2.start - 1)

            if prevtbg.tot_freq == 0:
                continue

            for mother, daughter in prevtbg.has_mother[
                                                argset['substrings']](dest):
                yield (mother, daughter, None)

    def iter_substitutions_growtbgs(self, argset):
        """Iterate through substitutions taken as changes from the cumulated
        previous time window. Yield (mother, string or substring, None)"""

        for qt2 in self.quotes.itervalues():
            dest = qt2.to_qt_string_lower(self.id)
            prevtbg = self.build_timebag(argset['n_timebags'], qt2.start - 1,
                                         True)
            if prevtbg.tot_freq == 0:
                continue

            for mother, daughter in prevtbg.has_mother[
                                                argset['substrings']](dest):
                yield (mother, daughter, None)

    def iter_substitutions_tbgs(self, argset):
        """Iterate through substitutions taken as changes between timebags.
        Yield (mother, string or substring, bag info) tuples."""
        tbgs = self.build_timebags(argset['n_timebags'])
        tot_freqs = [tbg.tot_freq for tbg in tbgs]
        idx = np.where(tot_freqs)[0]

        for i, j in zip(range(len(idx) - 1),
                        range(1, len(idx))):

            base = tbgs[idx[i]].qt_string_lower(tbgs[idx[i]].argmax_freq_string)
            for mother, daughter in tbgs[idx[j]].iter_sphere[
                                        argset['substrings']](base):
                yield (mother, daughter, {'bag1': idx[i], 'bag2': idx[j]})

    def iter_substitutions_cumtbgs(self, argset):
        """Iterate through substitutions taken as changes between cumulated
        timebags. Yield (mother, string or substring, bag info) tuples."""
        tbgs = self.build_timebags(argset['n_timebags'])
        cumtbgs = self.build_timebags(argset['n_timebags'], cumulative=True)
        tot_freqs = [tbg.tot_freq for tbg in tbgs]
        idx = np.where(tot_freqs)[0]

        for i, j in zip(range(len(idx) - 1),
                        range(1, len(idx))):

            base = cumtbgs[idx[i]].qt_string_lower(
                                            cumtbgs[idx[i]].argmax_freq_string)
            for mother, daughter in tbgs[idx[j]].iter_sphere[
                                        argset['substrings']](base):
                yield (mother, daughter, {'cumbag1': idx[i], 'bag2': idx[j]})

    def iter_substitutions_time(self, argset):
        """Iterate through substitutions taken as transitions from earlier quotes
        to older quotes (in order of appearance in time)."""

        distance_word_mother = {False: distance_word_mother_nosub,
                                True: distance_word_mother_sub}
        qt_list = []
        qt_starts = np.zeros(self.n_quotes)

        for i, qt in enumerate(self.quotes.itervalues()):

            qt.compute_attrs()
            qt_list.append(qt)
            qt_starts[i] = qt.start

        order = np.argsort(qt_starts)
        qt_starts = qt_starts[order]
        qt_list = [qt_list[order[i]] for i in range(self.n_quotes)]
        tuples = build_ordered_tuples(self.n_quotes)

        for i, j in tuples:

            base = qt_list[i].to_qt_string_lower(self.id)
            daughter = qt_list[j].to_qt_string_lower(self.id)
            d, mother = distance_word_mother[argset['substrings']](base, daughter)

            if d == 1:

                mother_start = qt_starts[i]
                daughter_start = qt_starts[j]
                mother_d = datetime.fromtimestamp(
                                    mother_start).strftime('%Y-%m-%d %H:%m:%S')
                daughter_d = datetime.fromtimestamp(
                                    daughter_start).strftime('%Y-%m-%d %H:%m:%S')
                yield (mother, daughter,
                    {'mother_start': mother_d,
                        'daughter_start': daughter_d})


class QtStringLinguistics(str):

    """Augment a string with POS tags, tokens, cluster id and quote id.

    Methods:
      * __init__: parse the string for POS tags and tokens, if asked to

    """

    def __new__(cls, string, cl_id=-1, qt_id=-1, parse=True):
        return super(QtStringLinguistics, cls).__new__(cls, string)

    def __init__(self, string, cl_id, qt_id, parse=True):
        """Parse the string for POS tags and tokens, if asked to ('parse'
        argument)."""
        self.cl_id = cl_id
        self.qt_id = qt_id
        if parse:
            self.POS_tags = tagger.Tags(string)
            self.tokens = tagger.Tokenize(string)

