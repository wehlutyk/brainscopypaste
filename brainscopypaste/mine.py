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
class Destination(Enum):
    all = 1
    exclude_past = 2


class Interval:

    def __init__(self, start, end):
        assert start <= end
        self.start = start
        self.end = end

    def __contains__(self, other):
        return self.start <= other < self.end


class Model:

    bin_span = timedelta(days=1)

    def __init__(self, time, source, past, destination):
        assert time in Time
        self.time = time
        assert source in Source
        self.source = source
        assert past in Past
        self.past = past
        assert destination in Destination
        self.destination = destination

        self._source_validation_table = {
            Source.all: self._ok,
            Source.majority: self._validate_source_majority
        }
        self._destination_validation_table = {
            Destination.all: self._ok,
            Destination.exclude_past: self._validate_destination_exclude_past
        }

    def __repr__(self):
        return ('Model(time={0.time}, source={0.source}, past={0.past}, '
                'destination={0.destination})').format(self)

    @memoized
    def validate(self, source, destination):
        # TODO: test
        return (self._validate_base(source, destination) and
                self._validate_source(source, destination) and
                self._validate_destination(source, destination))

    def _validate_base(self, source, destination):
        past = self._past(source.cluster, destination)
        return np.any([url.timestamp in past for url in source.urls])

    def _validate_source(self, source, destination):
        return self._source_validation_table[self.source](source, destination)

    def _validate_destination(self, source, destination):
        return self._destination_validation_table[self.destination](
            source, destination)

    def _ok(self, *args, **kwargs):
        return True

    def _validate_source_majority(self, source, destination):
        # TODO: test
        # - with source majority with all combinations of past/time
        # - with source non majority with all combinations of past/time
        # - with source ex-aequo majority with all combinations of past/time

        # Source must be a majority quote in `past`.
        past_quote_ids = np.array([quote.id for quote in
                                   self.past_quotes(source.cluster,
                                                    destination)])
        counts = dict((i, c) for (i, c) in
                      zip(*np.unique(past_quote_ids, return_counts=True)))
        return counts.get(source.id) == max(counts.values())

    def _validate_destination_exclude_past(self, source, destination):
        # TODO: test
        # - with destination in all combinations of past/time
        # - with destination not in all combinations of past/time
        # - with destination at seam of past/time

        # Destination must not be in `past`.
        return (destination.quote not in
                self.past_quotes(source.cluster, destination))

    @memoized
    def past_quotes(self, cluster, destination):
        # TODO: test
        past = self._past(cluster, destination)
        return set(url.quote for url in cluster.urls if url.timestamp in past)

    @memoized
    def _past(self, cluster, destination):
        # TODO: test
        # - with Time.continuous, Time.discrete, Past.all, Past.last_bin
        # - with destination at bin seam
        # - with destination the very first occurrence of the cluster
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
            end = destination.timestamp
        else:
            # Time is discrete.
            previous_bin_count = (destination.timestamp -
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
        self.past_quotes.drop_cache()
        self._past.drop_cache()


class ClusterMinerMixin:

    def substitutions(self, model):
        # TODO: test
        # - decide behaviour for multiple frequencies of urls

        # Iterate through candidate substitutions.
        for destination in self.urls:
            for source in model.past_quotes(self, destination):
                # Don't test against ourselves.
                if destination.quote == source:
                    continue

                # We allow for substrings.
                distance, start = subhamming(source.lemmas,
                                             destination.quote.lemmas)

                # Check distance, source and destination validity.
                if distance == 1 and model.validate(source, destination):
                    yield self._substitution(source, destination, start, model)

    def _substitution(self, source, destination, start, model):
        # TODO: test
        from brainscopypaste.db import Substitution

        dlemmas = destination.quote.lemmas
        slemmas = source.lemmas[start:start + len(dlemmas)]
        positions = np.where([c1 != c2
                              for (c1, c2) in zip(slemmas, dlemmas)])[0]
        assert len(positions) == 1
        return Substitution(source=source, destination=destination.quote,
                            occurrence=destination.occurrence,
                            start=int(start), position=int(positions[0]),
                            model=model)


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
