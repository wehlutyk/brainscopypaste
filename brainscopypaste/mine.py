"""Mine substitutions with various mining models.

This module defines several classes and mixins to mine substitutions in the
MemeTracker dataset with a series of different models.

:class:`Time`, :class:`Source`, :class:`Past` and :class:`Durl` together define
how a substitution :class:`Model` behaves. :class:`Interval` is a utility class
used internally in :class:`Model`. The :class:`ClusterMinerMixin` mixin builds
on this definition of a substitution model to provide
:meth:`ClusterMinerMixin.substitutions` which iterates over all valid
substitutions in a :class:`~.db.Cluster`. Finally,
:func:`mine_substitutions_with_model` brings :class:`ClusterMinerMixin` and
:class:`SubstitutionValidatorMixin` (which checks for spam substitutions)
together to mine for all substitutions in the dataset for a given
:class:`Model`.

"""


from enum import Enum, unique
from datetime import timedelta, datetime
import logging

import click
from progressbar import ProgressBar
import numpy as np
from nltk.corpus import wordnet

from brainscopypaste.conf import settings
from brainscopypaste.utils import (is_int, is_same_ending_us_uk_spelling,
                                   stopwords, levenshtein, subhamming,
                                   session_scope, memoized)


logger = logging.getLogger(__name__)


def mine_substitutions_with_model(model, limit=None):
    """Mine all substitutions in the MemeTracker dataset conforming to `model`.

    Iterates through the whole MemeTracker dataset to find all substitutions
    that are considered valid by `model`, and save the results to the database.
    The MemeTracker dataset must have been loaded and filtered previously, or
    an excetion will be raised (see :ref:`usage` or :mod:`.cli` for more about
    that). Mined substitutions are saved each time the function moves to a new
    cluster, and progress is printed to stdout. The number of substitutions
    seen and the number of substitutions kept (i.e. validated by
    :meth:`SubstitutionValidatorMixin.validate`) are also printed to stdout.

    Parameters
    ----------
    model : :class:`Model`
        The substitution model to use for mining.
    limit : int, optional
        If not `None` (default), mining will stop after `limit` clusters have
        been examined.

    Raises
    ------
    Exception
        If no filtered clusters are found in the database, or if there already
        are some substitutions from model `model` in the database.

    """

    from brainscopypaste.db import Cluster, Substitution

    logger.info('Mining clusters for substitutions')
    if limit is not None:
        logger.info('Mining is limited to %s clusters', limit)

    click.echo('Mining clusters for substitutions with {}{}...'
               .format(model, '' if limit is None
                       else ' (limit={})'.format(limit)))

    # Check we haven't already mined substitutions with this model.
    with session_scope() as session:
        substitution_count = session.query(Substitution)\
            .filter(Substitution.model == model).count()
        if substitution_count != 0:
            raise Exception(('The database already contains substitutions '
                             'mined with this model ({} - {} substitutions). '
                             'You should drop these before doing anything '
                             'else.'.format(model, substitution_count)))

    # Check clusters have been filtered.
    with session_scope() as session:
        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() == 0:
            raise Exception('Found no filtered clusters, aborting.')

        query = session.query(Cluster.id).filter(Cluster.filtered.is_(True))
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    logger.info('Got %s clusters to mine', len(cluster_ids))

    # Mine.
    seen = 0
    kept = 0
    for cluster_id in ProgressBar()(cluster_ids):
        model.drop_caches()
        with session_scope() as session:
            cluster = session.query(Cluster).get(cluster_id)
            for substitution in cluster.substitutions(model):
                seen += 1
                if substitution.validate():
                    logger.debug('Found valid substitution in cluster #%s',
                                 cluster.sid)
                    kept += 1
                    session.commit()
                else:
                    logger.debug('Dropping substitution from cluster #%s',
                                 cluster.sid)
                    session.rollback()

    # Sanity check. This session business is tricky.
    with session_scope() as session:
        assert session.query(Substitution)\
            .filter(Substitution.model == model).count() == kept

    click.secho('OK', fg='green', bold=True)
    logger.info('Seen %s candidate substitutions, kept %s', seen, kept)
    click.echo('Seen {} candidate substitutions, kept {}.'.format(seen, kept))


@unique
class Time(Enum):
    """Type of time that determines the positioning of occurrence bins."""

    #: Continuous time: bins are sliding, end at the destination occurrence,
    #: and start :attr:`Model.bin_span` before that.
    continuous = 1
    #: Discrete time: bins are aligned at midnight, end at or before the
    #: destination occurrence, and start :attr:`Model.bin_span` before that.
    discrete = 2


@unique
class Source(Enum):
    """Type of quotes accepted as substitution sources."""

    #: All quotes are potential sources for substitutions.
    all = 1
    #: Majority rule: only quotes that are the most frequent in the considered
    #: past bin can be the source of substitutions (note that several quotes in
    #: a single bin can have the same maximal frequency).
    majority = 2


@unique
class Past(Enum):
    """How far back in the past can a substitution find its source."""

    #: The past is everything: substitution sources can be in any bin preceding
    #: the destination occurrence (which is an interval that can end at
    #: midnight before the destination occurrence when using
    #: :attr:`Time.discrete`).
    all = 1
    #: The past is the last bin: substitution sources must be in the bin
    #: preceding the destination occurrence (which can end at midnight before
    #: the destination occurrence when using :attr:`Time.discrete`).
    last_bin = 2


@unique
class Durl(Enum):
    """Type of quotes accepted as substitution destinations."""

    #: All quotes are potential destinations for substitutions.
    all = 1
    #: Excluded past rule: only quotes that do not appear in what :class:`Time`
    #: and :class:`Past` define as "the past" can be the destination of a
    #: substitution.
    exclude_past = 2


class Interval:

    """Time interval defined by `start` and `end`
    :class:`~datetime.datetime`\ s.

    Parameters
    ----------
    start : :class:datetime.datetime
        The interval's start (or left) bound.
    end : :class:datetime.datetime
        The interval's end (or right) bound.

    Raises
    ------
    Exception
        If `start` is strictly after `end` in time.

    Examples
    --------
    Test if a :class:`~datetime.datetime` is in an interval:

    >>> from datetime import datetime
    >>> itv = Interval(datetime(2016, 7, 5, 12, 15, 5),
    ...                datetime(2016, 7, 9, 13, 30, 0))
    >>> datetime(2016, 7, 8) in itv
    True
    >>> datetime(2016, 8, 1) in itv
    False

    """

    def __init__(self, start, end):
        assert start <= end
        self.start = start
        self.end = end

    def __contains__(self, other):
        """Test if `other` is in this :class:`Interval`."""

        return self.start <= other < self.end

    def __key(self):
        """Unique identifier for this interval, used to compute e.g. equality
        between two :class:`Interval` instances."""

        return (self.start, self.end)

    def __eq__(self, other):
        """Determine if two instances represent the same interval (underlies
        e.g.  ``itv1 == itv2``)"""

        return self.__key() == other.__key()

    def __hash__(self):
        """Hash for this interval (makes this class hashable, so usable e.g. as
        dict keys)."""

        return hash(self.__key())

    def __repr__(self):
        """String representation of this interval."""

        return 'Interval(start={0.start}, end={0.end})'.format(self)


class Model:

    """Substitution mining model.

    A mining model is defined by the combination of one parameter for each of
    :class:`Time`, :class:`Source`, :class:`Past`, :class:`Durl`, and a maximum
    hamming distance between source string (or substring) and destination
    string. This class represents such a model. It defines a couple of utility
    functions used in :class:`ClusterMinerMixin` (:meth:`find_start` and
    :meth:`past_surls`), and a :meth:`validate` method which determines if a
    given substitution conforms to the model. Other methods, prefixed with an
    underscore, are utilities for the methods cited above.

    Parameters
    ----------
    time : :class:`Time`
        Type of time defining how occurrence bins of the model are positioned.
    source : :class:`Source`
        Type of quotes that the model accepts as substitution sources.
    past : :class:`Past`
        How far back does the model look for substitution sources.
    durl : :class:`Durl`
        Type of quotes that the model accepts as substitution destinations.
    max_distance : int
        Maximum number of substitutions between a source string (or substring)
        and a destination string that the model will detect.

    Raises
    ------
    Exception
        If `max_distance` is more than half of
        :data:`~.settings.MT_FILTER_MIN_TOKENS`.

    """

    #: Span of occurrence bins the model makes.
    bin_span = timedelta(days=1)

    def __init__(self, time, source, past, durl, max_distance):
        assert time in Time
        self.time = time
        assert source in Source
        self.source = source
        assert past in Past
        self.past = past
        assert durl in Durl
        self.durl = durl
        assert 0 < max_distance <= settings.MT_FILTER_MIN_TOKENS // 2
        self.max_distance = max_distance

        #: dict associating a :class:`Source` to its validation method.
        self._source_validation_table = {
            Source.all: self._ok,
            Source.majority: self._validate_source_majority
        }
        #: dict associating a :class:`Durl` to its validation method.
        self._durl_validation_table = {
            Durl.all: self._ok,
            Durl.exclude_past: self._validate_durl_exclude_past
        }

    def __repr__(self):
        """String representation of this model."""

        return ('Model(time={0.time}, source={0.source}, past={0.past}, '
                'durl={0.durl}, max_distance={0.max_distance})').format(self)

    @memoized
    def validate(self, source, durl):
        """Test if potential substitutions from `source` quote to `durl`
        destination url are valid for this model.

        This method is :func:`~.utils.memoized` for performance.

        Parameters
        ----------
        source : :class:`~.db.Quote`
            Candidate source quote for substitutions; the substitutions can be
            from a substring of `source.string`.
        durl : :class:`~.db.Url`
            Candidate destination url for the substitutions.

        Returns
        -------
        bool
            `True` if the proposed source and destination url are considered
            valid by this model, `False` otherwise.

        """

        return (self._validate_distance(source, durl) and
                self._validate_base(source, durl) and
                self._validate_source(source, durl) and
                self._validate_durl(source, durl))

    def _validate_distance(self, source, durl):
        """Check that `source` and `durl` differ by no more than
        `self.max_distance`."""

        return 0 < self._distance_start(source, durl)[0] <= self.max_distance

    def _validate_base(self, source, durl):
        """Check that `source` has at least one occurrence in what this model
        considers to be the past before `durl`."""

        past = self._past(source.cluster, durl)
        return np.any([url.timestamp in past for url in source.urls])

    def _validate_source(self, source, durl):
        """Check that `source` is an acceptable substitution source for this
        model.

        This method proxies to the proper validation method, depending on the
        value of `self.source`.

        """

        return self._source_validation_table[self.source](source, durl)

    def _validate_durl(self, source, durl):
        """Check that `durl` is an acceptable substitution destination
        occurrence for this model.

        This method proxies to the proper validation method, depending on the
        value of `self.durl`.

        """

        return self._durl_validation_table[self.durl](source, durl)

    def _ok(self, *args, **kwargs):
        """Dummy method used when a validation should always pass."""

        return True

    def _validate_source_majority(self, source, durl):
        """Check that `source` verifies the majority rule."""

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
        """Check that `durl` verifies the excluded past rule."""

        # Durl.quote must not be in `past`.
        past_quotes = [surl.quote for surl in
                       self.past_surls(source.cluster, durl)]
        return durl.quote not in past_quotes

    def _distance_start(self, source, durl):
        """Get a `(distance, start)` tuple indicating the minimal distance
        between `source` and `durl`, and the position of `source`'s substring
        that achieves that minimum.

        This is in fact an alias for what the model considers to be valid
        transformations and how to define them, but provides proper
        encapsulation of concerns.

        """

        # We allow for substrings.
        # Note here that there can be a difference in lemmas without
        # there being a difference in tokens, because of fluctuations
        # in lemmatization. This is caught later on in the validation
        # of substitutions (see SubstitutionValidatorMixin.validate()),
        # instead of making this function more complicated.
        return subhamming(source.lemmas, durl.quote.lemmas)

    def find_start(self, source, durl):
        """Get the position of the substring of `source` that achieves minimal
        distance to `durl`."""

        return self._distance_start(source, durl)[1]

    @memoized
    def past_surls(self, cluster, durl):
        """Get the list of all :class:`~.db.Url`\ s that are in what this model
        considers to be the past before `durl`.

        This method is :func:`~.utils.memoized` for performance.

        """

        past = self._past(cluster, durl)
        return list(filter(lambda url: url.timestamp in past, cluster.urls))

    @memoized
    def _past(self, cluster, durl):
        """Get an :class:`Interval` representing what this model considers to
        be the past before `durl`.

        See :class:`Time` and :class:`Past` to understand what this interval
        looks like. This method is :func:`~.utils.memoized` for performance.

        """

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
        """Drop the caches of all :func:`~.utils.memoized` methods of the
        class."""

        self.validate.drop_cache()
        self.past_surls.drop_cache()
        self._past.drop_cache()

    def __key(self):
        """Unique identifier for this model, used to compute e.g. equality
        between two :class:`Model` instances."""

        return (self.time, self.source, self.past, self.durl,
                self.max_distance)

    def __eq__(self, other):
        """Determine if two instances represent the same model (underlies
        e.g.  ``model1 == model2``)"""

        return hasattr(other, '_Model__key') and self.__key() == other.__key()

    def __hash__(self):
        """Hash for this model (makes this class hashable, so usable e.g. as
        dict keys)."""

        return hash(self.__key())


class ClusterMinerMixin:

    """Mixin for :class:`~.db.Cluster`\ s that provides substitution mining
    functionality.

    This mixin defines the :meth:`substitutions` method (based on the private
    :meth:`_substitutions` method) that iterates through all valid
    substitutions for a given :class:`Model`.

    """

    def substitutions(self, model):
        """Iterate through all substitutions in this cluster considered valid
        by `model`.

        Multiple occurrences of a sentence at the same url (url "frequency")
        are ignored, so as not to artificially inflate results.

        Parameters
        ----------
        model : :class:`Model`
            Model for which to mine substitutions in this cluster.

        Yields
        ------
        substitution : :class:`~.db.Substitution`
            All the substitutions in this cluster considered valid by `model`.
            When `model` allows for multiple substitutions between a quote and
            a destination url, each substitution is yielded individually. Any
            substitution yielded is attached to this cluster, so if you use
            this in a :func:`~.utils.session_scope` substitutions will be saved
            automatically unless you explicitly rollback the session.

        """

        # Iterate through candidate substitutions.
        for durl in self.urls:
            past_quotes_set = set([surl.quote for surl in
                                   model.past_surls(self, durl)])
            # Don't test against ourselves.
            past_quotes_set.discard(durl.quote)
            for source in past_quotes_set:
                # Source can't be shorter than destination
                if len(source.lemmas) < len(durl.quote.lemmas):
                    continue

                # Check distance, source and durl validity.
                if model.validate(source, durl):
                    logger.debug('Found candidate substitution(s) between '
                                 'quote #%s and durl #%s/%s', source.sid,
                                 durl.quote.sid, durl.occurrence)
                    for substitution in self._substitutions(source, durl,
                                                            model):
                        yield substitution

    @classmethod
    def _substitutions(cls, source, durl, model):
        """Iterate through all substitutions from `source` to `durl` considered
        valid by `model`.

        This method yields all the substitutions between `source` and `durl`
        when `model` allows for multiple substitutions.

        Parameters
        ----------
        source : :class:`~.db.Quote`
            Source for the substitutions.
        durl : :class:`~.db.Url`
            Destination url for the substitutions.
        model : :class:`Model`
            Model that validates the substitutions between `source` and `durl`.

        """

        from brainscopypaste.db import Substitution

        start = model.find_start(source, durl)
        dlemmas = durl.quote.lemmas
        slemmas = source.lemmas[start:start + len(dlemmas)]
        positions = np.where([c1 != c2
                              for (c1, c2) in zip(slemmas, dlemmas)])[0]
        assert 0 < len(positions) <= model.max_distance
        for position in positions:
            yield Substitution(source=source, destination=durl.quote,
                               occurrence=durl.occurrence, start=int(start),
                               position=int(position), model=model)


@memoized
def _get_wordnet_words():
    """Get the set of all words known by WordNet.

    This is the set of all lemma names for all synonym sets in WordNet.

    """

    return set(word.lower()
               for synset in wordnet.all_synsets()
               for word in synset.lemma_names())


class SubstitutionValidatorMixin:

    """Mixin for :class:`~.db.Substitution` that adds validation functionality.

    A non-negligible part of the substitutions found by
    :class:`ClusterMinerMixin` are spam or changes we're not interested in:
    minor spelling changes, abbreviations, changes of articles, symptoms of a
    deleted word that appear as substitutions, etc. This class defines the
    :meth:`validate` method, which tests for all these cases and returns
    whether or not the substitution is worth keeping.

    """

    def validate(self):
        """Check whether or not this substitution is worth keeping."""

        token1, token2 = self.tokens
        lem1, lem2 = self.lemmas
        tokens1, tokens2 = self.source.tokens, self.destination.tokens
        lemmas1, lemmas2 = self.source.lemmas, self.destination.lemmas

        # Only real-word lemmas.
        wordnet_words = _get_wordnet_words()
        if lem1 not in wordnet_words or lem2 not in wordnet_words:
            return False
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
        # Other minor spelling changes, also catching cases where tokens are
        # not different but lemmas are (because of lemmatization fluctuations).
        if levenshtein(token1, token2) <= 1:
            return False
        if levenshtein(lem1, lem2) <= 1:
            return False
        # Word deletion ('high school' -> 'school')
        if (self.start + self.position > 0 and
            (token2 == tokens1[self.start + self.position - 1] or
             lem2 == lemmas1[self.start + self.position - 1])):
            return False
        if (self.start + self.position < len(tokens1) - 1 and
            (token2 == tokens1[self.start + self.position + 1] or
             lem2 == lemmas1[self.start + self.position + 1])):
            return False
        # Word insertion ('school' -> 'high school')
        if (self.position > 0 and
            (token1 == tokens2[self.position - 1] or
             lem1 == lemmas2[self.position - 1])):
            return False
        if (self.position < len(tokens2) - 1 and
            (token1 == tokens2[self.position + 1] or
             lem1 == lemmas2[self.position + 1])):
            return False
        # Two words deletion ('supply of energy' -> 'supply')
        if (self.start + self.position > 1 and
            (token2 == tokens1[self.start + self.position - 2] or
             lem2 == lemmas1[self.start + self.position - 2])):
            return False
        if (self.start + self.position < len(tokens1) - 2 and
            (token2 == tokens1[self.start + self.position + 2] or
             lem2 == lemmas1[self.start + self.position + 2])):
            return False
        # Words stuck together ('policy maker' -> 'policymaker'
        # or 'policy-maker')
        if (self.start + self.position > 0 and
            (token2 == tokens1[self.start + self.position - 1] + token1 or
             token2 == tokens1[self.start + self.position - 1] +
                '-' + token1 or
             lem2 == lemmas1[self.start + self.position - 1] + lem1 or
             lem2 == lemmas1[self.start + self.position - 1] + '-' + lem1)):
            return False
        if (self.start + self.position < len(tokens1) - 1 and
            (token2 == token1 + tokens1[self.start + self.position + 1] or
             token2 == token1 + '-' +
                tokens1[self.start + self.position + 1] or
             lem2 == lem1 + lemmas1[self.start + self.position + 1] or
             lem2 == lem1 + '-' + lemmas1[self.start + self.position + 1])):
            return False
        # Words separated ('policymaker' or 'policy-maker' -> 'policy maker')
        if (self.position > 0 and
            (token1 == tokens2[self.position - 1] + token2 or
             token1 == tokens2[self.position - 1] + '-' + token2 or
             lem1 == lemmas2[self.position - 1] + lem2 or
             lem1 == lemmas2[self.position - 1] + '-' + lem2)):
            return False
        if (self.position < len(tokens2) - 1 and
            (token1 == token2 + tokens2[self.position + 1] or
             token1 == token2 + '-' + tokens2[self.position + 1] or
             lem1 == lem2 + lemmas2[self.position + 1] or
             lem1 == lem2 + '-' + lemmas2[self.position + 1])):
            return False
        # We need 2 extra checks compare to the words-stuck-together situation,
        # to detect teh second substitution appearing because of word
        # separation. Indeed in this case, contrary to words-stuck-together, we
        # can't rely on word shifts always being present, since the destination
        # can be cut shorter. In other words, in the following case:
        # (1) i'll come anytime there
        # (2) i'll come any time
        # these checks let us exclude 'there' -> 'time' as a substitution (in
        # the words-stuck-together case, the word 'there' would be present in
        # both sentences, shifted).
        if (self.position > 0 and
            (tokens1[self.start + self.position - 1] ==
                tokens2[self.position - 1] + token2 or
             tokens1[self.start + self.position - 1] ==
                tokens2[self.position - 1] + '-' + token2 or
             lemmas1[self.start + self.position - 1] ==
                lemmas2[self.position - 1] + lem2 or
             lemmas1[self.start + self.position - 1] ==
                lemmas2[self.position - 1] + '-' + lem2)):
            return False
        if (self.position < len(tokens2) - 1 and
            (tokens1[self.start + self.position + 1] ==
                token2 + tokens2[self.position + 1] or
             tokens1[self.start + self.position + 1] ==
                token2 + '-' + tokens2[self.position + 1] or
             lemmas1[self.start + self.position + 1] ==
                lem2 + lemmas2[self.position + 1] or
             lemmas1[self.start + self.position + 1] ==
                lem2 + '-' + lemmas2[self.position + 1])):
            return False

        return True
