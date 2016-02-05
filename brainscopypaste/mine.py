from enum import Enum, unique
from datetime import timedelta, datetime

import click
from progressbar import ProgressBar
import numpy as np

from brainscopypaste.utils import (is_int, is_same_ending_us_uk_spelling,
                                   stopwords, levenshtein, subhamming,
                                   session_scope, memoized)


def mine_substitutions_with_model(model, limit=None):
    # TODO: test
    from brainscopypaste.db import Cluster

    click.echo('Mining clusters for substitutions with {}{}...'
               .format(model, '' if limit is None else ' (test run)'))

    with session_scope() as session:
        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() == 0:
            raise Exception('Found no filtered clusters, aborting.')

        query = session.query(Cluster.id).filter(Cluster.filtered.is_(True))
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    seen = 0
    kept = 0
    for cluster_id in ProgressBar()(cluster_ids):
        with session_scope() as session:
            cluster = session.query(Cluster).get(cluster_id)
            for substitution in cluster.substitutions(model):
                seen += 1
                if substitution.validate():
                    kept += 1
                else:
                    session.rollback()

    click.secho('OK', fg='green', bold=True)
    click.echo('Seen {} candidate substitutions, kept {}.'.format(seen, kept))


@unique
class Time(Enum):
    continuous = 1
    discrete = 2


@unique
class Source(Enum):
    all = 1
    majority = 2


@unique
class Past(Enum):
    all = 1
    last_bin = 2


@unique
class Durl(Enum):
    all = 1
    exclude_past = 2


class Interval:

    def __init__(self, start, end):
        assert start <= end
        self.start = start
        self.end = end

    def __contains__(self, other):
        return self.start <= other < self.end

    def __repr__(self):
        return 'Interval(start={0.start}, end={0.end})'.format(self)


class Model:

    bin_span = timedelta(days=1)

    def __init__(self, time, source, past, durl):
        assert time in Time
        self.time = time
        assert source in Source
        self.source = source
        assert past in Past
        self.past = past
        assert durl in Durl
        self.durl = durl

        self._source_validation_table = {
            Source.all: self._ok,
            Source.majority: self._validate_source_majority
        }
        self._durl_validation_table = {
            Durl.all: self._ok,
            Durl.exclude_past: self._validate_durl_exclude_past
        }

    def __repr__(self):
        return ('Model(time={0.time}, source={0.source}, past={0.past}, '
                'durl={0.durl})').format(self)

    @memoized
    def validate(self, source, durl):
        # TODO: test
        return (self._validate_base(source, durl) and
                self._validate_source(source, durl) and
                self._validate_durl(source, durl))

    def _validate_base(self, source, durl):
        past = self._past(source.cluster, durl)
        return np.any([url.timestamp in past for url in source.urls])

    def _validate_source(self, source, durl):
        return self._source_validation_table[self.source](source, durl)

    def _validate_durl(self, source, durl):
        return self._durl_validation_table[self.durl](source, durl)

    def _ok(self, *args, **kwargs):
        return True

    def _validate_source_majority(self, source, durl):
        # Source must be a majority quote in `past`.
        past_quote_ids = np.array([surl.quote.id for surl in
                                   self.past_surls(source.cluster, durl)])
        if source.id not in past_quote_ids:
            return False

        counts = dict((i, c) for (i, c) in
                      zip(*np.unique(past_quote_ids, return_counts=True)))
        if len(counts) == 0:
            return False
        return counts[source.id] == max(counts.values())

    def _validate_durl_exclude_past(self, source, durl):
        # Durl.quote must not be in `past`.
        past_quotes = [surl.quote for surl in
                       self.past_surls(source.cluster, durl)]
        return durl.quote not in past_quotes

    @memoized
    def past_surls(self, cluster, durl):
        # TODO: test
        past = self._past(cluster, durl)
        return list(filter(lambda url: url.timestamp in past, cluster.urls))

    @memoized
    def _past(self, cluster, durl):
        # TODO: test
        # - with Time.continuous, Time.discrete, Past.all, Past.last_bin
        # - with durl at bin seam
        # - with durl the very first occurrence of the cluster
        cluster_start = min([url.timestamp for url in cluster.urls])
        # The bins are aligned to midnight, so get the midnight
        # before cluster start.
        cluster_bin_start = datetime(year=cluster_start.year,
                                     month=cluster_start.month,
                                     day=cluster_start.day)

        # Check our known `time` types.
        assert self.time in [Time.continuous, Time.discrete]
        if self.time is Time.continuous:
            # Time is continuous.
            end = durl.timestamp
        else:
            # Time is discrete.
            previous_bin_count = (durl.timestamp -
                                  cluster_bin_start) // self.bin_span
            end = max(cluster_start,
                      cluster_bin_start + previous_bin_count * self.bin_span)

        # Check our known `past` types.
        assert self.past in [Past.all, Past.last_bin]
        if self.past is Past.all:
            # The past is everything until the start of the cluster.
            start = cluster_start
        else:
            # The past is only the last bin.
            start = max(cluster_start, end - self.bin_span)

        return Interval(start, end)

    def drop_caches(self):
        self.validate.drop_cache()
        self.past_surls.drop_cache()
        self._past.drop_cache()


class ClusterMinerMixin:

    def substitutions(self, model):
        # TODO: test

        # Multiple occurrences of a sentence at the same url (url 'frequency')
        # are ignored, so as not to artificially inflate results.

        # Iterate through candidate substitutions.
        for durl in self.urls:
            past_quotes_set = set([surl.quote for surl in
                                   model.past_surls(self, durl)])
            for source in past_quotes_set:
                # Don't test against ourselves.
                if durl.quote == source:
                    continue

                # We allow for substrings.
                distance, start = subhamming(source.lemmas,
                                             durl.quote.lemmas)

                # Check distance, source and durl validity.
                if distance == 1 and model.validate(source, durl):
                    yield self._substitution(source, durl, start, model)

    def _substitution(self, source, durl, start, model):
        # TODO: test
        from brainscopypaste.db import Substitution

        dlemmas = durl.quote.lemmas
        slemmas = source.lemmas[start:start + len(dlemmas)]
        positions = np.where([c1 != c2
                              for (c1, c2) in zip(slemmas, dlemmas)])[0]
        assert len(positions) == 1
        return Substitution(source=source, destination=durl.quote,
                            occurrence=durl.occurrence, start=int(start),
                            position=int(positions[0]), model=model)


class SubstitutionValidatorMixin:

    def validate(self):
        # TODO: test

        token1, token2 = self.tokens
        lem1, lem2 = self.lemmas

        # '21st'/'twenty-first', etc.
        if (is_int(token1[0]) or is_int(token2[0]) or
                is_int(lem1[0]) or is_int(lem2[0])):
            return False
        # 'sen'/'senator', 'gov'/'governor', 'nov'/'november', etc.
        if (token1 == token2[:3] or token2 == token1[:3] or
                lem1 == lem2[:3] or lem2 == lem1[:3]):
            return False
        # 'programme'/'program', etc.
        if (token1[:-2] == token2 or token2[:-2] == token1 or
                lem1[:-2] == lem2 or lem2[:-2] == lem1):
            return False
        # 'centre'/'center', etc.
        if is_same_ending_us_uk_spelling(token1, token2):
            return False
        if is_same_ending_us_uk_spelling(lem1, lem2):
            return False
        # stopwords
        if (token1 in stopwords or token2 in stopwords or
                lem1 in stopwords or lem2 in stopwords):
            return False
        # Other minor spelling changes
        if levenshtein(token1, token2) <= 1:
            return False
        if levenshtein(lem1, lem2) <= 1:
            return False

        return True
