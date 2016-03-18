import logging
from csv import DictReader

import numpy as np
from nltk.corpus import cmudict, wordnet

from brainscopypaste.utils import is_int, memoized, unpickle
from brainscopypaste.paths import pickled_features, aoa_Kuperman_csv


logger = logging.getLogger(__name__)


@memoized
def _get_pronunciations():
    logger.debug('Loading CMU data')
    return cmudict.dict()


@memoized
def _get_aoa():
    logger.debug('Loading Age-of-Acquisition data')

    aoa = {}
    with open(aoa_Kuperman_csv) as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            if row['Rating.Mean'] == 'NA':
                continue
            aoa[row['Word']] = float(row['Rating.Mean'])
    return aoa


class SubstitutionFeaturesMixin:

    __features__ = {
        'syllables_count': 'tokens',
        'phonemes_count': 'tokens',
        'letters_count': 'tokens',
        'synonyms_count': 'lemmas',
        'aoa': 'lemmas',
        'fa_degree': 'lemmas',
        'fa_pagerank': 'lemmas',
        'fa_betweenness': 'lemmas',
        'fa_clustering': 'lemmas',
        'frequency': 'lemmas',
        'phonological_density': 'lemmas',
    }

    @memoized
    def features(self, name, sentence_relative=False):
        if name not in self.__features__:
            raise ValueError("Unknown feature: '{}'".format(name))

        # Get the substitution's tokens or lemmas,
        # depending on the requested feature.
        source_type = self.__features__[name]
        word1, word2 = getattr(self, source_type)

        # Compute the features.
        feature = getattr(self, '_' + name)
        feature1, feature2 = feature(word1), feature(word2)

        if sentence_relative:
            # Substract the average sentence feature.
            destination_words = getattr(self.destination, source_type)
            source_words = getattr(self.source, source_type)[
                self.start:self.start + len(destination_words)]
            feature1 -= np.nanmean([feature(word) for word
                                    in source_words])
            feature2 -= np.nanmean([feature(word) for word
                                    in destination_words])

        return (feature1, feature2)

    @classmethod
    @memoized
    def feature_h0(self, name, neighbour_range=None):
        # TODO: implement
        raise NotImplementedError

    @classmethod
    @memoized
    def _syllables_count(self, word):
        pronunciations = _get_pronunciations()
        if word not in pronunciations:
            return np.nan
        return np.mean([sum([is_int(ph[-1]) for ph in pronunciation])
                        for pronunciation in pronunciations[word]])

    @classmethod
    @memoized
    def _phonemes_count(self, word):
        pronunciations = _get_pronunciations()
        if word not in pronunciations:
            return np.nan
        return np.mean([len(pronunciation)
                        for pronunciation in pronunciations[word]])

    @classmethod
    @memoized
    def _letters_count(self, word):
        return len(word)

    @classmethod
    @memoized
    def _synonyms_count(self, word):
        synsets = wordnet.synsets(word)
        if len(synsets) == 0:
            return np.nan
        count = np.mean([len(synset.lemmas()) - 1 for synset in synsets])
        return count if count != 0 else np.nan

    @classmethod
    @memoized
    def _aoa(self, word):
        aoa = _get_aoa()
        return aoa.get(word)

    @classmethod
    @memoized
    def _fa_degree(self, word):
        # TODO: test with found and not found word
        # TODO: test it's done on lemmas, not tokens
        raise NotImplementedError
        fa_degree = unpickle(pickled_features['fa_degree'])
        return fa_degree.get(word)

    @classmethod
    @memoized
    def _fa_pagerank(self, word):
        # TODO: test with found and not found word
        # TODO: test it's done on lemmas, not tokens
        raise NotImplementedError
        fa_pagerank = unpickle(pickled_features['fa_pagerank'])
        return fa_pagerank.get(word)

    @classmethod
    @memoized
    def _fa_betweenness(self, word):
        # TODO: test with found and not found word
        # TODO: test it's done on lemmas, not tokens
        raise NotImplementedError
        fa_betweenness = unpickle(pickled_features['fa_betweenness'])
        return fa_betweenness.get(word)

    @classmethod
    @memoized
    def _fa_clustering(self, word):
        # TODO: test with found and not found word
        # TODO: test it's done on lemmas, not tokens
        raise NotImplementedError
        fa_clustering = unpickle(pickled_features['fa_clustering'])
        return fa_clustering.get(word)

    @classmethod
    @memoized
    def _frequency(self, word):
        # TODO: test with found and not found word
        # TODO: test it's done on lemmas, not tokens
        raise NotImplementedError
        frequency = unpickle(pickled_features['frequency'])
        return frequency.get(word)

    @classmethod
    @memoized
    def _phonological_density(self, word):
        # TODO: find a database
        raise NotImplementedError
