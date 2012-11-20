import numpy as np

from datetime import datetime

from linguistics.treetagger import tagger
from util.combinatorials import build_ordered_tuples
from linguistics.distance import (distance_word_mother_nosub,
                                  distance_word_mother_sub,
                                  levenshtein, levenshtein_word,
                                  hamming, hamming_word,
                                  subhamming, subhamming_word)
import datastructure.base as ds_mtb


class QuoteModels(ds_mtb.QuoteBase):

        def to_qt_string_lower(self, cl_id, parse=True):
            """Return a QtString built from this Quote, in lowercase."""
            from datastructure.full import QtString
            return QtString(self.string.lower(), cl_id, self.id, parse=parse)


class QtStringModels(str):

    """Augment a string with POS tags, tokens, cluster id and quote id.

    Methods:
      * __init__: parse the string for POS tags and tokens, if asked to

    """

    def __new__(cls, string, cl_id=-1, qt_id=-1, parse=True):
        return super(QtStringModels, cls).__new__(cls, string)

    def __init__(self, string, cl_id, qt_id, parse=True):
        """Parse the string for POS tags and tokens, if asked to ('parse'
        argument)."""
        self.cl_id = cl_id
        self.qt_id = qt_id
        if parse:
            self.POS_tags = tagger.Tags(string)
            self.tokens = tagger.Tokenize(string)


class ClusterModels(ds_mtb.ClusterBase):

    def __init__(self, *args, **kwargs):
        super(ClusterModels, self).__init__(*args, **kwargs)

    def build_timebags(self, n_bags, cumulative=False):
        """Build a number of TimeBags from a Cluster.

        Arguments:
        * n_bags: the number of TimeBags to chop the Cluster into

        Keyword arguments:
        * cumulative: boolean specifying if the timebags built should be
                        time-cumulative or not. Defaults to False.

        Returns: a list of TimeBags.

        """

        import datastructure.full as ds_mt

        # Build the Timeline for the Cluster, set the parameters for the TimeBags.

        self.build_timeline()

        step = int(round(self.timeline.span.total_seconds() / n_bags))
        cl_start = self.timeline.start

        # Create the sequence of TimeBags.

        timebags = []
        dontcum = not cumulative

        for i in xrange(n_bags):
            timebags.append(ds_mt.TimeBag(self, cl_start + i * step * dontcum,
                                        cl_start + (i + 1) * step))

        return timebags

    def build_timebag(self, n_bags, end, cumulative=False):
        """Build a TimeBag from a Cluster.

        Arguments:
        * n_bags: the number of TimeBags we're slicing the cluster into
        * end: the timestamp at which the timebag should end

        Keyword arguments:
        * cumulative: boolean specifying if the timebag built should be
                        time-cumulative or not. If True, the timebag built
                        starts at the beginning of the cluster, else it starts
                        at `end - cluster_span / n_bags`. Defaults to False.

        """

        import datastructure.full as ds_mt

        # Build the timeline for the Cluster, set the parameters for the
        # TimeBag

        self.build_timeline()
        cl_start = self.timeline.start

        if not cumulative:

            span = int(round(self.timeline.span.total_seconds() / n_bags))
            start = max(cl_start, end - span)

        else:
            start = cl_start

        return ds_mt.TimeBag(self, start, end)

    @property
    def iter_substitutions(self):
        return ds_mtb.dictionarize_attributes(self, 'iter_substitutions_')

    def iter_substitutions_root(self, ma):
        """Iterate through substitutions taken as changes from root string. Yield
        (mother, string or substring, bag info) tuples."""

        # This import goes here to prevent a circular import problem.

        from datastructure.full import QtString

        base = QtString(self.root.lower(), self.id, 0)
        tbgs = self.build_timebags(ma.n_timebags)

        for j in range(0, ma.n_timebags):

            for mother, daughter in tbgs[j].iter_sphere[ma.substrings](base):
                yield (mother, daughter, {'tobag': j})

    def iter_substitutions_slidetbgs(self, ma):
        """Iterate through substitutions taken as changes from the preceding
        time window. Yield (mother, string or substring, None) tuples."""

        for qt2 in self.quotes.itervalues():

            dest = qt2.to_qt_string_lower(self.id)
            for url_time in qt2.url_times:

                prevtbg = self.build_timebag(ma.n_timebags, url_time)
                if prevtbg.tot_freq == 0:
                    continue

                for mother, daughter in prevtbg.has_mother[ma.substrings](dest):
                    yield (mother, daughter, None)

    def iter_substitutions_growtbgs(self, ma):
        """Iterate through substitutions taken as changes from the cumulated
        previous time window. Yield (mother, string or substring, None)"""

        for qt2 in self.quotes.itervalues():

            dest = qt2.to_qt_string_lower(self.id)
            for url_time in qt2.url_times:

                prevtbg = self.build_timebag(ma.n_timebags, url_time, True)
                if prevtbg.tot_freq == 0:
                    continue

                for mother, daughter in prevtbg.has_mother[ma.substrings](dest):
                    yield (mother, daughter, None)

    def iter_substitutions_tbgs(self, ma):
        """Iterate through substitutions taken as changes between timebags.
        Yield (mother, string or substring, bag info) tuples."""
        tbgs = self.build_timebags(ma.n_timebags)
        tot_freqs = [tbg.tot_freq for tbg in tbgs]
        idx = np.where(tot_freqs)[0]

        for i, j in zip(range(len(idx) - 1),
                        range(1, len(idx))):

            base = tbgs[idx[i]].qt_string_lower(tbgs[idx[i]].argmax_freq_string)
            for mother, daughter in tbgs[idx[j]].iter_sphere[ma.substrings](base):
                yield (mother, daughter, {'bag1': idx[i], 'bag2': idx[j]})

    def iter_substitutions_cumtbgs(self, ma):
        """Iterate through substitutions taken as changes between cumulated
        timebags. Yield (mother, string or substring, bag info) tuples."""
        tbgs = self.build_timebags(ma.n_timebags)
        cumtbgs = self.build_timebags(ma.n_timebags, cumulative=True)
        tot_freqs = [tbg.tot_freq for tbg in tbgs]
        idx = np.where(tot_freqs)[0]

        for i, j in zip(range(len(idx) - 1),
                        range(1, len(idx))):

            base = cumtbgs[idx[i]].qt_string_lower(
                                            cumtbgs[idx[i]].argmax_freq_string)
            for mother, daughter in tbgs[idx[j]].iter_sphere[ma.substrings](base):
                yield (mother, daughter, {'cumbag1': idx[i], 'bag2': idx[j]})

    def iter_substitutions_time(self, ma):
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

    def __init__(self, *args, **kwargs):
        super(TimeBagModels, self).__init__(*args, **kwargs)
        self.iter_sphere = {False: self.iter_sphere_nosub,
                            True: self.iter_sphere_sub}
        self.has_mother = {False: self.has_mother_nosub,
                           True: self.has_mother_sub}

    def qt_string_lower(self, k, parse=True):
        """Return a QtString corresponding to string number k of the Timebag,
        in lowercase."""
        from datastructure.full import QtString
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
        """Iterate through strings in timebag in a sphere centered at 'base'.
        Yield (mother, string) tuples."""
        for k in self.hamming_word_sphere(base, 1):
            yield (base, self.qt_string_lower(k))

    def iter_sphere_sub(self, base):
        """Iterate through strings in timebag in a subsphere centered at
        'base'. Yield the (effective mother, substring) tuples."""

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


