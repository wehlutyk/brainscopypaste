#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Reconstruct the source-destination information missing in the MemeTracker
dataset.

The MemeTracker includes only clustered quotes, as well as urls and timestamps
for those quotes, but no information on where a quote was taken from when it
appears in a blog or media outlet (this is because most posters don't cite
their source, it's not the practice). But if we are to detect sustitutions from
one quote to another, we must know wich substitution came from which other.

So there is a reconstruction process involved, where we assume a few additional
hypotheses to be able to connect each quote to a parent one. This can be done
with a variety of hypotheses, each set leading to a reconstruction model. You
can mine for substitutions using any one of these models.

"""


from __future__ import division

import numpy as np

from datetime import datetime

from linguistics.treetagger import get_tagger
from util.combinatorials import build_ordered_tuples
from util.generic import dictionarize_attributes
from linguistics.distance import (distance_word_mother_nosub,
                                  distance_word_mother_sub,
                                  levenshtein, levenshtein_word,
                                  hamming, hamming_word,
                                  subhamming, subhamming_word)
import datastructure.base as ds_mtb


class QuoteModels(ds_mtb.QuoteBase):

    """Mixin class for :class:`~datastructure.base.QuoteBase` to easily build
    a :class:`~datastructure.full.QtString`.

    See Also
    --------
    datastructure.base.QuoteBase, datastructure.full.Quote,
    datastructure.full.QtString

    """

    def to_qt_string_lower(self, cl_id, parse=True):
        """Return a :class:`~datastructure.full.QtString` built from this
        :class:`~datastructure.full.Quote`, in lowercase.

        Parameters
        ----------
        cl_id : int
            The cluster id to include in the new
            :class:`~datastructure.full.QtString`.
        parse : bool, optional
            Whether to parse the newly created
            :class:`~datastructure.full.QtString` for POS tags and tokens,
            or not; defaults to ``True``.

        Returns
        -------
        QtString
            The newly created :class:`~datastructure.full.QtString`.

        See Also
        --------
        datastructure.full.Quote, datastructure.full.QtString

        """

        from datastructure.full import QtString
        return QtString(self.string.lower(), cl_id, self.id, parse=parse)


class QtStringModels(str):

    """Mixin class to augment a string with POS tags, tokens,
    cluster id and quote id.

    This class adds a few attributes to a regular python string, giving quick
    access to the parent cluster id, the id of the quote this string was taken
    from, as well as the POS tags, tokens, and lemmas in the string.

    Parameters
    ----------
    string : string
        The string to be augmented to a :class:`QtString`.
    cl_id : int, optional
        The id of the :class:`~datastructure.full.Cluster` the quote was
        taken from; defaults to -1.
    qt_id : int, optional
        The id of the :class:`~datastructure.full.Quote` the string
        represents; defaults to -1.
    parse : bool
        Whether or not to parse `string` to extract POS tags, tokens, and
        lemmas; defaults to ``True``.

    Attributes
    ----------
    cl_id : int
        The id of the parent :class:`~datastructure.full.Cluster`.
    qt_id : int
        The id of the parent :class:`~datastructure.full.Quote`.
    POS_tags : list of strings
        The list of POS tags extracted from the string, if parsing was
        activated upon creation.
    tokens : list of strings
        The list of tokens extracted from the string, if parsing was
        activated upon creation.
    lemmas : list of strings
        The list of lemmas extracted from the string, if parsing was
        activated upon creation.

    See Also
    --------
    datastructure.full.QtString

    """

    def __new__(cls, string, cl_id=-1, qt_id=-1, parse=True):
        return super(QtStringModels, cls).__new__(cls, string)

    def __init__(self, string, cl_id, qt_id, parse=True):
        """Create the QtString and possibly parse the corresponding string
        for POS tags and tokens.

        Parameters
        ----------
        string : string
            The string to be augmented to a :class:`QtString`.
        cl_id : int, optional
            The id of the :class:`~datastructure.full.Cluster` the quote was
            taken from; defaults to -1.
        qt_id : int, optional
            The id of the :class:`~datastructure.full.Quote` the string
            represents; defaults to -1.
        parse : bool
            Whether or not to parse `string` to extract POS tags, tokens, and
            lemmas; defaults to ``True``.

        """

        tagger = get_tagger()
        self.cl_id = cl_id
        self.qt_id = qt_id
        if parse:
            self.POS_tags = tagger.Tags(string)
            self.tokens = tagger.Tokenize(string)
            self.lems = tagger.Lemmatize(string)


class ClusterModels(ds_mtb.ClusterBase):

    """Mixin class providing methods to iterate through substitutions
    according to a given source-destination model.

    See :class:`~datastructure.base.ClusterBase` for init parameters, and
    attributes.

    See Also
    --------
    datastructure.base.ClusterBase, datastructure.full.Cluster

    """

    def __init__(self, *args, **kwargs):
        super(ClusterModels, self).__init__(*args, **kwargs)

    def build_timebags(self, bag_duration, cumulative=False):
        """Build a number of even :class:`~datastructure.full.TimeBag`\ s from
        a :class:`~datastructure.full.Cluster` (all even except the last).

        Parameters
        ----------
        bag_duration : float
            The default duration, in days, of the
            :class:`~datastructure.full.TimeBag`\ s to build from the
            :class:`~datastructure.full.Cluster` (if not cumulative; if
            `cumulative` is ``True``, this parameter specifies the increment
            size for each timebag)
        cumulative : bool, optional
            Whether or not the :class:`~datastructure.full.TimeBag`\ s should
            be time-cumulative or not; defaults to ``False``.

        Returns
        -------
        list
            The list of :class:`~datastructure.full.TimeBag`\ s built.

        """

        import datastructure.full as ds_mt

        # Build the Timeline for the Cluster, set the parameters for the
        # TimeBags.

        self.build_timeline()

        step = int(round(bag_duration * 60 * 60 * 24))
        total_seconds = int(self.timeline.span.total_seconds())
        n_bags = (total_seconds // step) + (total_seconds % step > 0)
        cl_start = self.timeline.start

        # Create the sequence of TimeBags.

        timebags = []
        dontcum = not cumulative

        for i in xrange(n_bags):
            timebags.append(ds_mt.TimeBag(self, cl_start + i * step * dontcum,
                                          cl_start + (i + 1) * step))

        return timebags

    def build_timebag(self, bag_duration, end, cumulative=False):
        """Build a :class:`~datastructure.full.TimeBag` from a
        :class:`~datastructure.full.Cluster`, ending at a chosen time.

        Parameters
        ----------
        bag_duration : float
            The default duration of the :class:`~datastructure.full.TimeBag`
            to be built (if not cumulative; if `cumulative` is ``True``, this
            parameter is ignored).
        end : int
            The timestamp at which the :class:`~datastructure.full.TimeBag`
            should end.
        cumulative : bool, optional
            Whether or not the :class:`~datastructure.full.TimeBag` built
            should be time-cumulative or not; if ``True``, the timebag built
            starts at the beginning of the cluster, otherwise it starts at
            `end - bag_duration`; defaults to ``False``.

        Returns
        -------
        TimeBag
            The built timebag.

        """

        import datastructure.full as ds_mt

        # Build the timeline for the Cluster, set the parameters for the
        # TimeBag

        self.build_timeline()
        cl_start = self.timeline.start

        if not cumulative:
            start = max(cl_start, end - bag_duration)
        else:
            start = cl_start

        return ds_mt.TimeBag(self, start, end)

    @property
    def iter_substitutions(self):
        """A dict of methods keyed by the different models available
        to iterate over substitutions.

        The dict includes all the methods defined in this class whose name
        starts with `iter_substitutions_`. So you can use it as::

            c = Cluster(...)      # Create a cluster (missing parameters)
            ma = MiningArgs(...)  # Create a set of mining arguments
            c.iter_substitutions['cumtbgs'](ma)  # Iterate over substitutions
            # by using the 'cumtbgs' source-destination model and the provided
            # mining arguments.

        """

        return dictionarize_attributes(self, 'iter_substitutions_')

    def iter_substitutions_root(self, ma):
        """Iterate through substitutions taken as changes from root string.

        This iterator will yield `(effective mother, string or substring
        of the original mother, timebag info)` tuples.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

        # This import goes here to prevent a circular import problem.

        from datastructure.full import QtString

        base = QtString(self.root.lower(), self.id, 0)
        tbgs = self.build_timebags(ma.timebag_size)
        # If we don't have at least one timebag, there's no point going on.
        if len(tbgs) == 0:
            return

        for j, tbg in enumerate(tbgs):

            for mother, daughter in tbg.iter_sphere[ma.substrings](base):
                yield (mother, daughter, {'tobag': j})

    def iter_substitutions_slidetbgs(self, ma):
        """Iterate through substitutions taken as changes from the preceding
        time window.

        This iterator will yield `(effective mother, string or substring
        of the original mother, None)` tuples.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

        for qt2 in self.quotes.itervalues():

            dest = qt2.to_qt_string_lower(self.id)
            for url_time in qt2.url_times:

                prevtbg = self.build_timebag(ma.timebag_size, url_time)
                # If no quotes were found in the previous time window, we
                # consider qt2 to have appeared from elsewhere, instead of
                # from an even earlier time window.
                if prevtbg.tot_freq == 0:
                    continue

                for mother, daughter in prevtbg.has_mother[
                        ma.substrings](dest):
                    yield (mother, daughter, None)

    def iter_substitutions_growtbgs(self, ma):
        """Iterate through substitutions taken as changes from the cumulated
        previous time window.

        This iterator will yield `(effective mother, string or substring of
        the original mother, None)` tuples.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

        for qt2 in self.quotes.itervalues():

            dest = qt2.to_qt_string_lower(self.id)
            for url_time in qt2.url_times:

                prevtbg = self.build_timebag(ma.timebag_size, url_time, True)
                # If no quotes were found in the previous time window, we
                # consider qt2 to have appeared from elsewhere (there's no
                # other possible explanation here, since the timebags are
                # cumulative).
                if prevtbg.tot_freq == 0:
                    continue

                for mother, daughter in prevtbg.has_mother[
                        ma.substrings](dest):
                    yield (mother, daughter, None)

    def iter_substitutions_tbgs(self, ma):
        """Iterate through substitutions taken as changes between timebags.

        This iterator will yield `(effective mother, string or substring of
        the original mother, timebag info)` tuples.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

        tbgs = self.build_timebags(ma.timebag_size)
        n_bags = len(tbgs)
        # If we don't have at least two timebags, there's no point going on.
        if n_bags <= 1:
            return

        tot_freqs = [tbg.tot_freq for tbg in tbgs]

        for i in range(n_bags - 1):
            # If there are no quotes in either the first or the second timebag,
            # we consider that there has been no substitution (instead of
            # having substitutions that jump over empty timebags).
            if tot_freqs[i] == 0 or tot_freqs[i + 1] == 0:
                continue

            base = tbgs[i].qt_string_lower(tbgs[i].argmax_freq_string)
            for mother, daughter in tbgs[i + 1].iter_sphere[
                    ma.substrings](base):
                yield (mother, daughter, {'bag1': i, 'bag2': i + 1})

    def iter_substitutions_cumtbgs(self, ma):
        """Iterate through substitutions taken as changes between cumulated
        timebags.

        This iterator will yield `(effective mother, string or substring of
        the original mother, timebag info)` tuples.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

        tbgs = self.build_timebags(ma.timebag_size)
        n_bags = len(tbgs)
        # If we don't have at least two timebags, there's no point going on.
        if n_bags <= 1:
            return

        cumtbgs = self.build_timebags(ma.timebag_size, cumulative=True)
        tot_freqs = [tbg.tot_freq for tbg in tbgs]
        tot_cumfreqs = [cumtbg.tot_freq for cumtbg in cumtbgs]

        for i in range(n_bags - 1):
            # If there are no quotes in either the first or the second timebag,
            # we consider that there has been no substitution (instead of
            # having substitutions that jump over empty timebags).
            if tot_cumfreqs[i] == 0 or tot_freqs[i + 1] == 0:
                continue

            base = cumtbgs[i].qt_string_lower(cumtbgs[i].argmax_freq_string)
            for mother, daughter in tbgs[i + 1].iter_sphere[
                    ma.substrings](base):
                yield (mother, daughter, {'cumbag1': i, 'bag2': i + 1})

    def iter_substitutions_time(self, ma):
        """Iterate through substitutions taken as transitions from earlier
        quotes to older quotes (in order of appearance in time).

        This iterator will yield `(effective mother, string or substring of the
        original mother, info dict)`, where the info dict contains two keys:
        `mother_start` and `daughter_start`, specifying the timestamp at
        which the mother and daughter respectively first started appearing
        in the dataset.

        Parameters
        ----------
        ma : :class:`~.args.MiningArgs`
            The set of mining arguments to follow.

        """

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
            d, mother = distance_word_mother[ma.substrings](base, daughter)

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


class TimeBagModels(ds_mtb.TimeBagBase):

    """Mixin class to find substrings and strings at a given distance of a
    given string in a :class:`~datastructure.full.TimeBag`.

    See :class:`~datastructure.base.TimeBagBase` for init parameters and
    base attributes.

    Attributes
    ----------
    iter_sphere : dict
        Association of the mining args `substrings` parameter to the right \
        `iter_sphere_*` method; for instance, if mining args say to look \
        at substrings, you can use ``self.iter_sphere[ma.substrings]`` to \
        call `self.iter_sphere_sub`.
    has_mother : dict
        Association of the mining args `substrings` parameter to the right \
        `has_mother_**` method; for instance, if mining args say to look \
        at substrings, you can use ``self.has_mother[ma.substrings]`` to \
        call `self.has_mother_sub`.

    See Also
    --------
    datastructure.base.TimeBagBase, datastructure.full.TimeBag

    """

    def __init__(self, *args, **kwargs):
        """Initialize the structure from super and add the `iter_sphere` and
        `has_mother` dicts of methods."""

        super(TimeBagModels, self).__init__(*args, **kwargs)
        self.iter_sphere = {False: self.iter_sphere_nosub,
                            True: self.iter_sphere_sub}
        self.has_mother = {False: self.has_mother_nosub,
                           True: self.has_mother_sub}

    def qt_string_lower(self, k, parse=True):
        """Build a parsed :class:`~datastructure.full.QtString` corresponding
        to string number `k` of the timebag, in lowercase."""

        from datastructure.full import QtString
        return QtString(self.strings[k].lower(), self.id_fromcluster,
                        self.ids[k], parse=parse)

    def levenshtein_sphere(self, center_string, d):
        """Get the indexes of the strings in the timebag that are at
        `levenshtein-distance == d` from `center_string`."""

        distances = np.array([levenshtein(center_string, bag_string)
                              for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def levenshtein_word_sphere(self, center_string, d):
        """Get the indexes of the strings in the timebag that are at
        `levenshtein_word-distance == d` from `center_string`."""

        distances = np.array([levenshtein_word(center_string, bag_string)
                              for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def hamming_sphere(self, center_string, d):
        """Get the indexes of the strings in the timebag that are at
        `hamming-distance == d` from `center_string`."""

        distances = np.array([hamming(center_string, bag_string)
                              for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def hamming_word_sphere(self, center_string, d):
        """Get the indexes of the strings in the timebag that are at
        `hamming_word-distance == d` from `center_string`."""

        distances = np.array([hamming_word(center_string, bag_string)
                              for bag_string in self.strings])

        idx = np.where(distances == d)

        if len(idx) > 0:
            return idx[0].tolist()
        else:
            return []

    def subhamming_sphere(self, center_string, d):
        """Get the indices and motherstrings of the substrings in the timebag
        that are at `subhamming-distance == d` from `center_string`."""

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
        """Get the indices and motherstrings of the substrings in the timebag
        that are at `subhamming_word-distance == d` from `center_string`."""

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
        """Test if this timebag's max freq string is a nosub mother for `dest`;
        if so, yield a `(mother, daughter)` tuple; else return."""

        base = self.qt_string_lower(self.argmax_freq_string)
        if hamming_word(base, dest) == 1:
            yield (base, dest)

    def has_mother_sub(self, dest):
        """Test if this timebag's max freq string is a sub mother for `dest`;
        if so, yield an `(effective mother, daughter)` tuple; else return."""

        import datastructure.full as ds_mt

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
        """Iterate through strings in the timebag that are in a sphere
        centered at `base`, yielding `(mother, string)` tuples."""

        for k in self.hamming_word_sphere(base, 1):
            yield (base, self.qt_string_lower(k))

    def iter_sphere_sub(self, base):
        """Iterate through strings in the timebag that are in a subsphere
        centered at `base`, yielding the `(effective mother, substring)`
        tuples."""

        # This import goes here to prevent a circular import problem.

        from datastructure.full import QtString

        for k, m in self.subhamming_word_sphere(base, 1):

            mother_tok = base.tokens[m[0]:m[0] + m[1]]
            mother_pos = base.POS_tags[m[0]:m[0] + m[1]]
            mother = QtString(' '.join(mother_tok), base.cl_id, base.qt_id,
                              parse=False)
            mother.tokens = mother_tok
            mother.POS_tags = mother_pos
            yield (mother, self.qt_string_lower(k))
