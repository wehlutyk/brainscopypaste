"""Features for words in substitutions.

This module defines the :class:`SubstitutionFeaturesMixin` which is used to
augment :class:`~.db.Substitution`\ s with convenience methods that give access
to feature values and related computed values (e.g. sentence-relative feature
values and values for composite features).

A few other utility functions that load data for the features are also defined.

"""


import logging
from csv import DictReader, reader as csvreader
import warnings
import functools

import numpy as np
from nltk.corpus import cmudict, wordnet

from brainscopypaste.utils import is_int, memoized, unpickle
from brainscopypaste.conf import settings


logger = logging.getLogger(__name__)


@memoized
def _get_pronunciations():
    """Get the CMU pronunciation data as a dict.

    Returns
    -------
    dict
        Association of words to their list of possible pronunciations.

    """

    logger.debug('Loading CMU data')
    return cmudict.dict()


@memoized
def _get_aoa():
    """Get the Age-of-Acquisition data as a dict.

    Returns
    -------
    dict
        Association of words to their average age of acquisition. `NA` values
        in the originating data set are ignored.

    """

    logger.debug('Loading Age-of-Acquisition data')

    aoa = {}
    with open(settings.AOA) as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            word = row['Word'].lower()
            mean = row['Rating.Mean']
            if mean == 'NA':
                continue
            if word in aoa:
                raise Exception("'{}' is already is AoA dictionary"
                                .format(word))
            aoa[word] = float(mean)
    return aoa


@memoized
def _get_clearpond():
    """Get CLEARPOND neighbourhood density data as a dict.

    Returns
    -------
    dict
        `Dict` with two keys: `orthographic` and `phonological`. `orthographic`
        contains a dict associating words to their orthographic neighbourhood
        density (CLEARPOND's `OTAN` column). `phonological` contains a dict
        associating words to their phonological neighbourhood density
        (CLEARPOND's `PTAN` column).

    """

    logger.debug('Loading Clearpond data')

    clearpond_orthographic = {}
    clearpond_phonological = {}
    with open(settings.CLEARPOND, encoding='iso-8859-2') as csvfile:
        reader = csvreader(csvfile, delimiter='\t')
        for row in reader:
            word = row[0].lower()
            if word in clearpond_phonological:
                raise Exception("'{}' is already is Clearpond phonological "
                                'dictionary'.format(word))
            if word in clearpond_orthographic:
                raise Exception("'{}' is already is Clearpond orthographic "
                                'dictionary'.format(word))
            clearpond_orthographic[word] = int(row[5])
            clearpond_phonological[word] = int(row[29])
    return {'orthographic': clearpond_orthographic,
            'phonological': clearpond_phonological}


class SubstitutionFeaturesMixin:

    """Mixin for :class:`~.db.Substitution`\ s adding feature-related
    functionality.

    Methods in this class fall into 3 categories:

    * Raw feature methods: they are :class:`~.utils.memoized` class methods of
      the form `cls._feature_name(cls, word=None)`. Calling them with a `word`
      returns either the feature value of that word, or `np.nan` if the word is
      not encoded. Calling them with `word=None` returns the set of words
      encoded by that feature (which is used to compute e.g. averages over the
      pool of words encoded by that feature). Their docstring (which you will
      see below if you're reading this in a web browser) is the short name used
      to identify e.g. the feature's column in analyses in notebooks. These
      methods are used internally by the class, to provide the next category of
      methods.
    * Useful feature methods that can be used in analyses: :meth:`features`,
      :meth:`feature_average`, :meth:`source_destination_features`,
      :meth:`components`, and :meth:`component_average`. These methods use the
      raw feature methods (previous category) and the utility methods (next
      category) to compute feature or composite values (eventually relative to
      sentence) on the source or destination words or sentences.
    * Private utility methods: :meth:`_component`,
      :meth:`_source_destination_components`, :meth:`_average`,
      :meth:`_static_average`, :meth:`_strict_synonyms`,
      :meth:`_substitution_features`, and :meth:`_transformed_feature`. These
      methods are used by the previous category of methods.

    Read the source of the first category (raw features) to know how exactly an
    individual feature is computed. Read the docstrings (and source) of the
    second category (useful methods for analyses) to learn how to use this
    class in analyses. Read the docstrings (and source) of the third category
    (private utility methods) to learn how the whole class assembles its
    different parts together.

    """

    #: Association of available features to `(source_type, transform)` tuples:
    #: `source_type` defines if a feature is computed on tokens or lemmas, and
    #: `transform` defines how a feature value is transformed (for now either
    #: identity or log) because of the shape of its distribution (see the
    #: `notebook/feature_distributions.ipynb` notebook for more details).
    __features__ = {
        # feature_name:           (source_type, transform)
        'syllables_count':        ('tokens', lambda x: x),
        'phonemes_count':         ('tokens', lambda x: x),
        'letters_count':          ('tokens', lambda x: x),
        'synonyms_count':         ('lemmas', np.log),
        'aoa':                    ('lemmas', lambda x: x),
        'degree':                 ('lemmas', np.log),
        'pagerank':               ('lemmas', np.log),
        'betweenness':            ('lemmas', np.log),
        'clustering':             ('lemmas', np.log),
        'frequency':              ('lemmas', np.log),
        'phonological_density':   ('tokens', np.log),
        'orthographic_density':   ('tokens', np.log),
    }

    @memoized
    def _substitution_features(self, name):
        if name not in self.__features__:
            raise ValueError("Unknown feature: '{}'".format(name))

        # Get the substitution's tokens or lemmas,
        # depending on the requested feature.
        source_type, _ = self.__features__[name]
        word1, word2 = getattr(self, source_type)

        # Compute the features.
        feature = self._transformed_feature(name)
        return feature(word1), feature(word2)

    @memoized
    def source_destination_features(self, name, sentence_relative=None):
        if name not in self.__features__:
            raise ValueError("Unknown feature: '{}'".format(name))

        # Get the source and destination tokens or lemmas,
        # depending on the requested feature.
        source_type, _ = self.__features__[name]
        destination_words = getattr(self.destination, source_type)
        source_words = getattr(self.source, source_type)[
            self.start:self.start + len(destination_words)]

        # Compute the features.
        feature = self._transformed_feature(name)
        source_features = np.array([feature(word) for word
                                    in source_words],
                                   dtype=np.float_)
        destination_features = np.array([feature(word) for word
                                         in destination_words],
                                        dtype=np.float_)

        if sentence_relative is not None:
            pool = getattr(np, 'nan' + sentence_relative)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                source_features -= pool(source_features)
                destination_features -= pool(destination_features)

        return source_features, destination_features

    @memoized
    def features(self, name, sentence_relative=None):
        feature1, feature2 = self._substitution_features(name)

        if sentence_relative is not None:
            pool = getattr(np, 'nan' + sentence_relative)
            source_features, destination_features = \
                self.source_destination_features(name)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                feature1 -= pool(source_features)
                feature2 -= pool(destination_features)

        return feature1, feature2

    @memoized
    def _source_destination_components(self, n, pca, feature_names):
        # Check the PCA was computed for as many features as we're given.
        n_features = len(feature_names)
        assert n_features == len(pca.mean_)

        # First compute the matrices of word, feature for source and
        # destination.
        n_words = len(self.destination.tokens)
        source_features = np.zeros((n_words, n_features), dtype=np.float_)
        destination_features = np.zeros((n_words, n_features), dtype=np.float_)
        for j, name in enumerate(feature_names):
            source_features[:, j], destination_features[:, j] = \
                self.source_destination_features(name)
        # Then transform those into components, guarding for NaNs.
        source_components = np.zeros(n_words, dtype=np.float_)
        destination_components = np.zeros(n_words, dtype=np.float_)
        for i in range(n_words):
            source_components[i] = \
                pca.transform(source_features[i, :].reshape(1, -1))[0, n]\
                if np.isfinite(source_features[i, :]).all() else np.nan
            destination_components[i] = \
                pca.transform(destination_features[i, :]
                              .reshape(1, -1))[0, n]\
                if np.isfinite(destination_features[i, :]).all() else np.nan

        return source_components, destination_components

    @memoized
    def components(self, n, pca, feature_names, sentence_relative=None):
        # Check the PCA was computed for as many features as we're given.
        n_features = len(feature_names)
        assert n_features == len(pca.mean_)

        # Compute the features, and transform into components.
        features = np.zeros((2, n_features), dtype=np.float_)
        for j, name in enumerate(feature_names):
            features[:, j] = self._substitution_features(name)
        components = np.zeros(2, dtype=np.float_)
        for i in range(2):
            components[i] = pca.transform(features[i, :].reshape(1, -1))[0, n]\
                if np.isfinite(features[i, :]).all() else np.nan

        if sentence_relative is not None:
            pool = getattr(np, 'nan' + sentence_relative)
            # Substract the sentence average from substitution components.
            source_components, destination_components = \
                self._source_destination_components(n, pca, feature_names)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                components[0] -= pool(source_components)
                components[1] -= pool(destination_components)

        return components

    @classmethod
    @memoized
    def _static_average(cls, func):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)
            return np.nanmean([func(word) for word in func()])

    @memoized
    def _average(self, func, source_synonyms):
        if source_synonyms:
            # We always use the lemmas (vs. tokens) here, for two reasons:
            # - WordNet lemmatizes when looking for synsets (although it
            #   lemmatizes with wordnet.morphy(), not with treetagger, so there
            #   may be some differences when the feature is computed on lemmas)
            # - It's the only way to compute averages of components. Otherwise
            #   we're facing a different set of synonyms (those from the lemma
            #   and those from the token) for each feature used in the
            #   component, and it's impossible to bring them together.
            source_lemma, _ = self.lemmas
            # Assumes func() yields the set of words from which to compute
            # the average.
            words = self._strict_synonyms(source_lemma)

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                return np.nanmean([func(word) for word in words])
        else:
            return self._static_average(func)

    @memoized
    def feature_average(self, name, source_synonyms=False,
                        sentence_relative=None):
        """Compute the average of feature `name` over all coded words.

        If `source_synonyms` is `True`, the method computes the average feature
        of the synonyms of the source word of this substitution.  Otherwise, it
        computes the average over all words coded by the feature.

        If `sentence_relative` is not `None`, it is used to aggregate feature
        values of the words in the source sentence of this substitution, and
        this method returns the feature average minus that aggregate value.
        For instance, if `sentence_relative=np.median`, `feature_average`
        returns the average feature minus the median feature value in the
        sentence (words in the sentence valued at `np.nan` are ignored).

        Parameters
        ----------
        name : str
            Name of the feature for which to compute an average.
        source_synonyms : bool, optional
            If `True`, compute the average feature of the synonyms of the
            source word in this substitution. If `False` (default), compute the
            average over all coded words.
        sentence_relative : aggregating function, optional
            If not `None` (which is the default), return average feature
            relative to feature values of the sentence aggregated by this
            function.

        Returns
        -------
        float
            Average feature, of all coded words or of synonyms of the
            substitution's source word (depending on `source_synonyms`),
            relative to an aggregated sentence value if `sentence_relative`
            specifies it.

        """

        tfeature = self._transformed_feature(name)
        avg = self._average(tfeature, source_synonyms)

        if sentence_relative is not None:
            pool = getattr(np, 'nan' + sentence_relative)
            sentence_features, _ = self.source_destination_features(name)
            sentence_features[self.position] = avg
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                avg -= pool(sentence_features)

        return avg

    @memoized
    def component_average(self, n, pca, feature_names,
                          source_synonyms=False, sentence_relative=None):
        """Compute the average, over all coded words, of component `n` of `pca`
        using `feature_names`.

        If `source_synonyms` is `True`, the method computes the average
        component of the synonyms of the source word of this substitution.
        Otherwise, it computes the average over all words coded by the
        component.

        If `sentence_relative` is not `None`, it is used to aggregate component
        values of the words in the source sentence of this substitution, and
        this method returns the component average minus that aggregate value.
        For instance, if `sentence_relative=np.median`, `component_average`
        returns the average component minus the median component value in the
        sentence (words in the sentence valued at `np.nan` are ignored).

        Parameters
        ----------
        n : int
            Index of the component in `pca` that is to be computed.
        pca : :class:`sklearn.decomposition.PCA`
            :class:`~sklearn.decomposition.PCA` instance that was computed
            using the features listed in `feature_names`.
        feature_names : tuple of str
            Tuple of feature names used in the computation of `pca`.
        source_synonyms : bool, optional
            If `True`, compute the average component of the synonyms of the
            source word in this substitution. If `False` (default), compute the
            average over all coded words.
        sentence_relative : aggregating function, optional
            If not `None` (which is the default), return average component
            relative to component values of the sentence aggregated by this
            function.

        Returns
        -------
        float
            Average component, of all coded words or of synonyms of the
            substitution's source word (depending on `source_synonyms`),
            relative to an aggregated sentence value if `sentence_relative`
            specifies it.

        """

        component = self._component(n, pca, feature_names)
        avg = self._average(component, source_synonyms)

        if sentence_relative is not None:
            pool = getattr(np, 'nan' + sentence_relative)
            sentence_components, _ = \
                self._source_destination_components(n, pca, feature_names)
            sentence_components[self.position] = avg
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                avg -= pool(sentence_components)

        return avg

    @classmethod
    @memoized
    def _component(cls, n, pca, feature_names):
        """Get a function computing component `n` of `pca` using `feature_names`.

        Parameters
        ----------
        n : int
            Index of the component in `pca` that is to be computed.
        pca : :class:`sklearn.decomposition.PCA`
            :class:`~sklearn.decomposition.PCA` instance that was computed
            using the features listed in `feature_names`.
        feature_names : tuple of str
            Tuple of feature names used in the computation of `pca`.

        Returns
        -------
        component : function
            The component function, with signature `component(word=None)`. Call
            `component()` to get the set of words encoded by that component
            (which is the set of words encoded by all features in
            `feature_names`). Call `component(word)` to get the component value
            of `word` (or `np.nan` if `word` is not coded by that component).

        Examples
        --------
        Get the first component of "dog" in a PCA with very few words, using
        features `aoa`, `frequency`, and `letters_count`:

        >>> mixin = SubstitutionFeaturesMixin()
        >>> feature_names = ('aoa', 'frequency', 'letters_count')
        >>> features = list(map(mixin._transformed_feature,
        ...                     feature_names))
        >>> values = np.array([[f(w) for f in features]
        ...                    for w in ['bird', 'cat', 'human']])
        >>> from sklearn.decomposition import PCA
        >>> pca = PCA(n_components=2)
        >>> pca.fit(values)
        >>> mixin._component(0, pca, feature_names)('dog')
        -0.14284518091970733

        """

        # Check the PCA was computed for as many features as we're given.
        n_features = len(feature_names)
        assert n_features == len(pca.mean_)

        # Prepare our target words and component.
        # This sort of thing cannot be used for self.components() because each
        # feature uses either tokens or lemmas (here we use all words
        # indiscriminately).
        # Note that by doing this, we ignore the fact that a feature can yield
        # real values on words that don't appear in feature() (i.e. its base
        # set of words), in which case the average is a bit changed. Only
        # letters_count and synonyms are susceptible to this (because they're
        # not based on a dict). So we consider that the approach taken here is
        # fair to compute component average.
        tfeatures = [cls._transformed_feature(name) for name in feature_names]
        words = set()
        for tfeature in tfeatures:
            words.update(tfeature())

        def transform(word_tfeatures):
            """Get component `n` of `pca` based on a list of transformed word
            feature values; returns `np.nan` if some feature values are
            `np.nan`."""

            return pca.transform(word_tfeatures.reshape(1, -1))[0, n]\
                if np.isfinite(word_tfeatures).all() else np.nan

        def component(word=None):
            if word is None:
                return words
            else:
                word_tfeatures = np.array([tf(word) for tf in tfeatures],
                                          dtype=np.float_)
                return transform(word_tfeatures)

        # Set the right docstring and name on the component function.
        component.__name__ = '_component_{}'.format(n)
        component.__doc__ = 'component {}'.format(n)

        return component

    @classmethod
    @memoized
    def _transformed_feature(cls, name):
        """Get a function computing feature `name`, transformed as defined by
        :attr:`__features__`.

        Some features have a very skewed distribution (e.g. exponential, where
        a few words are valued orders of magnitude more than the vast majority
        of words), so we use their log-transformed values in the analysis to
        make them comparable to more regular features. The :attr:`__features__`
        attribute (which appears in the source code but not in the web version
        of these docs) defines which features are transformed how. Given a
        feature `name`, this method will generate a function that proxies calls
        to the raw feature method, and transforms the value if necessary.

        This method is :meth:`~.utils.memoized` for speed, since other methods
        call it all the time.

        Parameters
        ----------
        name : str
            Name of the feature for which to create a function, without
            preceding underscore; for instance, call
            `cls._transformed_feature('aoa')` to get a function that uses the
            :meth:`_aoa` class method.

        Returns
        -------
        feature : function
            The feature function, with signature `feature(word=None)`. Call
            `feature()` to get the set of words encoded by that feature. Call
            `feature(word)` to get the transformed feature value of `word` (or
            `np.nan` if `word` is not coded by that feature).

        Examples
        --------
        Get the transformed frequency value of "dog":

        >>> mixin = SubstitutionFeaturesMixin()
        >>> logfrequency = mixin._transformed_feature('frequency')
        >>> logfrequency('dog') == np.log(mixin._frequency('dog'))
        True

        """

        if name not in cls.__features__:
            raise ValueError("Unknown feature: '{}'".format(name))
        _feature = getattr(cls, '_' + name)
        _, transform = cls.__features__[name]

        def feature(word=None):
            if word is None:
                return _feature()
            else:
                return transform(_feature(word))

        # Set the right docstring and name on the transformed feature function.
        functools.update_wrapper(feature, _feature)
        if transform is np.log:
            feature.__name__ = '_log' + feature.__name__
            feature.__doc__ = 'log(' + feature.__doc__ + ')'

        return feature

    @classmethod
    def _strict_synonyms(cls, word):
        """Get the set of synonyms of `word` through WordNet, excluding `word`
        itself; empty if nothing is found."""

        # wordnet.synsets() lemmatizes words, so we might as well control it.
        # This also lets us check the lemma is present in the generated
        # synonym list further down.
        lemma = wordnet.morphy(word)
        if lemma is None:
            return set()

        synonyms = set(word.lower() for synset in wordnet.synsets(lemma)
                       for word in synset.lemma_names())
        if len(synonyms) > 0:
            assert lemma in synonyms
            synonyms.remove(lemma)
        return synonyms

    @classmethod
    @memoized
    def _syllables_count(cls, word=None):
        """<#syllables>"""
        pronunciations = _get_pronunciations()
        if word is None:
            return pronunciations.keys()
        if word not in pronunciations:
            return np.nan
        return np.mean([sum([is_int(ph[-1]) for ph in pronunciation])
                        for pronunciation in pronunciations[word]])

    @classmethod
    @memoized
    def _phonemes_count(cls, word=None):
        """<#phonemes>"""
        pronunciations = _get_pronunciations()
        if word is None:
            return pronunciations.keys()
        if word not in pronunciations:
            return np.nan
        return np.mean([len(pronunciation)
                        for pronunciation in pronunciations[word]])

    @classmethod
    @memoized
    def _letters_count(cls, word=None):
        """#letters"""
        if word is None:
            return unpickle(settings.TOKENS)
        return len(word)

    @classmethod
    @memoized
    def _synonyms_count(cls, word=None):
        """<#synonyms>"""
        if word is None:
            return set(word.lower()
                       for synset in wordnet.all_synsets()
                       for word in synset.lemma_names())
        synsets = wordnet.synsets(word)
        if len(synsets) == 0:
            return np.nan
        count = np.mean([len(synset.lemmas()) - 1 for synset in synsets])
        return count or np.nan

    @classmethod
    @memoized
    def _aoa(cls, word=None):
        """age of acquisition"""
        aoa = _get_aoa()
        if word is None:
            return aoa.keys()
        return aoa.get(word, np.nan)

    @classmethod
    @memoized
    def _degree(cls, word=None):
        """degree"""
        degree = unpickle(settings.DEGREE)
        if word is None:
            return degree.keys()
        return degree.get(word, np.nan)

    @classmethod
    @memoized
    def _pagerank(cls, word=None):
        """pagerank"""
        pagerank = unpickle(settings.PAGERANK)
        if word is None:
            return pagerank.keys()
        return pagerank.get(word, np.nan)

    @classmethod
    @memoized
    def _betweenness(cls, word=None):
        """betweenness"""
        betweenness = unpickle(settings.BETWEENNESS)
        if word is None:
            return betweenness.keys()
        return betweenness.get(word, np.nan)

    @classmethod
    @memoized
    def _clustering(cls, word=None):
        """clustering"""
        clustering = unpickle(settings.CLUSTERING)
        if word is None:
            return clustering.keys()
        return clustering.get(word, np.nan)

    @classmethod
    @memoized
    def _frequency(cls, word=None):
        """frequency"""
        frequency = unpickle(settings.FREQUENCY)
        if word is None:
            return frequency.keys()
        return frequency.get(word, np.nan)

    @classmethod
    @memoized
    def _phonological_density(cls, word=None):
        """phonological nd"""
        clearpond_phonological = _get_clearpond()['phonological']
        if word is None:
            return clearpond_phonological.keys()
        return clearpond_phonological.get(word, np.nan) or np.nan

    @classmethod
    @memoized
    def _orthographic_density(cls, word=None):
        """orthographic nd"""
        clearpond_orthographic = _get_clearpond()['orthographic']
        if word is None:
            return clearpond_orthographic.keys()
        return clearpond_orthographic.get(word, np.nan) or np.nan
