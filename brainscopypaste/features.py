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
    logger.debug('Loading CMU data')
    return cmudict.dict()


@memoized
def _get_aoa():
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
    logger.debug('Loading Clearpond data')

    clearpond_orthographical = {}
    clearpond_phonological = {}
    with open(settings.CLEARPOND, encoding='iso-8859-2') as csvfile:
        reader = csvreader(csvfile, delimiter='\t')
        for row in reader:
            word = row[0].lower()
            if word in clearpond_phonological:
                raise Exception("'{}' is already is Clearpond phonological "
                                'dictionary'.format(word))
            if word in clearpond_orthographical:
                raise Exception("'{}' is already is Clearpond orthographical "
                                'dictionary'.format(word))
            clearpond_orthographical[word] = int(row[5])
            clearpond_phonological[word] = int(row[29])
    return {'orthographical': clearpond_orthographical,
            'phonological': clearpond_phonological}


class SubstitutionFeaturesMixin:

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
        'orthographical_density': ('tokens', np.log),
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
    def _source_destination_features(self, name):
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
        return source_features, destination_features

    @memoized
    def features(self, name, sentence_relative=False):
        feature1, feature2 = self._substitution_features(name)

        if sentence_relative:
            source_features, destination_features = \
                self._source_destination_features(name)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                feature1 -= np.nanmean(source_features)
                feature2 -= np.nanmean(destination_features)

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
                self._source_destination_features(name)
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
    def components(self, n, pca, feature_names, sentence_relative=False):
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

        if sentence_relative:
            # Substract the sentence average from substitution components.
            source_components, destination_components = \
                self._source_destination_components(n, pca, feature_names)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                components[0] -= np.nanmean(source_components)
                components[1] -= np.nanmean(destination_components)

        return components

    @memoized
    def _average(self, func, source_synonyms):
        # We always use the lemmas (vs. tokens) here, for two reasons:
        # - WordNet lemmatizes when looking for synsets (although it lemmatizes
        #   with wordnet.morphy(), not with treetagger, so there may be some
        #   differences when the feature is computed on lemmas)
        # - It's the only way to compute averages of components. Otherwise
        #   we're facing a different set of synonyms (those from the lemma and
        #   those from the token) for each feature used in the component, and
        #   it's impossible to bring them together.
        source_lemma, _ = self.lemmas
        # Assumes func() yields the set of words from which to compute
        # the average.
        words = self._strict_synonyms(source_lemma) \
            if source_synonyms else func()

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)
            return np.nanmean([func(word) for word in words])

    @memoized
    def feature_average(self, name, source_synonyms=False,
                        sentence_relative=False):
        tfeature = self._transformed_feature(name)
        avg = self._average(tfeature, source_synonyms)

        if sentence_relative:
            sentence_features, _ = self._source_destination_features(name)
            sentence_features[self.position] = avg
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                avg -= np.nanmean(sentence_features)

        return avg

    @memoized
    def component_average(self, n, pca, feature_names,
                          source_synonyms=False, sentence_relative=False):
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
        tfeatures = [self._transformed_feature(name) for name in feature_names]
        words = set()
        for tfeature in tfeatures:
            words.update(tfeature())

        def transform(word_tfeatures):
            return pca.transform(word_tfeatures.reshape(1, -1))[0, n]\
                if np.isfinite(word_tfeatures).all() else np.nan

        def component(word=None):
            if word is None:
                return words
            else:
                word_tfeatures = np.array([tf(word) for tf in tfeatures],
                                          dtype=np.float_)
                return transform(word_tfeatures)

        avg = self._average(component, source_synonyms)

        if sentence_relative:
            sentence_components, _ = \
                self._source_destination_components(n, pca, feature_names)
            sentence_components[self.position] = avg
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                avg -= np.nanmean(sentence_components)

        return avg

    @classmethod
    @memoized
    def _transformed_feature(cls, name):
        if name not in cls.__features__:
            raise ValueError("Unknown feature: '{}'".format(name))
        _feature = getattr(cls, '_' + name)
        _, transform = cls.__features__[name]

        def feature(word=None):
            if word is None:
                return _feature()
            else:
                return transform(_feature(word))

        functools.update_wrapper(feature, _feature)
        if transform is np.log:
            feature.__name__ = '_log' + feature.__name__
            feature.__doc__ = 'log(' + feature.__doc__ + ')'

        return feature

    @classmethod
    def _strict_synonyms(cls, word):
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
    def _orthographical_density(cls, word=None):
        """orthographical nd"""
        clearpond_orthographical = _get_clearpond()['orthographical']
        if word is None:
            return clearpond_orthographical.keys()
        return clearpond_orthographical.get(word, np.nan) or np.nan
