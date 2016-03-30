import logging
from csv import DictReader, reader as csvreader
import warnings

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
        'syllables_count': 'tokens',
        'phonemes_count': 'tokens',
        'letters_count': 'tokens',
        'synonyms_count': 'lemmas',
        'aoa': 'lemmas',
        'degree': 'lemmas',
        'pagerank': 'lemmas',
        'betweenness': 'lemmas',
        'clustering': 'lemmas',
        'frequency': 'lemmas',
        'phonological_density': 'tokens',
        'orthographical_density': 'tokens',
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
    def feature_average(cls, name, synonyms_from_range=None):
        feature = getattr(cls, '_' + name)
        if synonyms_from_range is None:
            return np.nanmean([feature(word) for word in feature()])

        # Computing for synonyms of words with feature in the given range.
        min, max = synonyms_from_range
        base_words = [word for word in feature()
                      if min <= feature(word) < max]

        # Suppress warning here, see
        # http://stackoverflow.com/questions/29688168/mean-nanmean-and-warning-mean-of-empty-slice#29688390
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)

            # Average feature of synonyms, for each base word.
            base_averages = []
            for base_word in base_words:
                features = [feature(word) for word
                            in cls._strict_synonyms(base_word)]
                base_averages.append(np.nanmean(features))

            return np.nanmean(base_averages)

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
        if word is None:
            return unpickle(settings.TOKENS)
        return len(word)

    @classmethod
    @memoized
    def _synonyms_count(cls, word=None):
        if word is None:
            return set(word.lower()
                       for synset in wordnet.all_synsets()
                       for word in synset.lemma_names())
        synsets = wordnet.synsets(word)
        if len(synsets) == 0:
            return np.nan
        count = np.mean([len(synset.lemmas()) - 1 for synset in synsets])
        return count if count != 0 else np.nan

    @classmethod
    @memoized
    def _aoa(cls, word=None):
        aoa = _get_aoa()
        if word is None:
            return aoa.keys()
        return aoa.get(word, np.nan)

    @classmethod
    @memoized
    def _degree(cls, word=None):
        degree = unpickle(settings.DEGREE)
        if word is None:
            return degree.keys()
        return degree.get(word, np.nan)

    @classmethod
    @memoized
    def _pagerank(cls, word=None):
        pagerank = unpickle(settings.PAGERANK)
        if word is None:
            return pagerank.keys()
        return pagerank.get(word, np.nan)

    @classmethod
    @memoized
    def _betweenness(cls, word=None):
        betweenness = unpickle(settings.BETWEENNESS)
        if word is None:
            return betweenness.keys()
        return betweenness.get(word, np.nan)

    @classmethod
    @memoized
    def _clustering(cls, word=None):
        clustering = unpickle(settings.CLUSTERING)
        if word is None:
            return clustering.keys()
        return clustering.get(word, np.nan)

    @classmethod
    @memoized
    def _frequency(cls, word=None):
        frequency = unpickle(settings.FREQUENCY)
        if word is None:
            return frequency.keys()
        return frequency.get(word, np.nan)

    @classmethod
    @memoized
    def _phonological_density(cls, word=None):
        clearpond_phonological = _get_clearpond()['phonological']
        if word is None:
            return clearpond_phonological.keys()
        return clearpond_phonological.get(word, np.nan)

    @classmethod
    @memoized
    def _orthographical_density(cls, word=None):
        clearpond_orthographical = _get_clearpond()['orthographical']
        if word is None:
            return clearpond_orthographical.keys()
        return clearpond_orthographical.get(word, np.nan)
