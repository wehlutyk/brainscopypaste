#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Detect the language in a text using NLTK, detect stopwords.

Language detection is adapted from
https://github.com/vandanab/LangDetect written by vandanab.

"""


from __future__ import division

from nltk.util import trigrams as nltk_trigrams
from nltk.tokenize import word_tokenize as nltk_word_tokenize
from nltk.probability import FreqDist
from nltk.corpus.util import LazyCorpusLoader
from nltk.corpus.reader.api import CorpusReader
from nltk.corpus.reader.util import StreamBackedCorpusView, concat

from util.generic import memoize
import settings as st


class StopwordsDetector(object):

    """Detect if a word is a stopword."""

    def __init__(self):
        """Read and load stopwords file."""

        self.stopwords_file = st.stopwords_file
        self.stopwords = set([])
        with open(self.stopwords_file) as f:
            for l in f:
                self.stopwords.add(l.strip().lower())

    def __call__(self, word):
        """Is `word` a stopword or not."""

        return word in self.stopwords


class LangIdCorpusReader(CorpusReader):

    """LangID corpus reader."""

    CorpusView = StreamBackedCorpusView

    def _get_trigram_weight(self, line):
        """Split a line in a trigram and its frequency count."""

        data = line.strip().split(' ')

        if len(data) == 2:
            return (data[1], int(data[0]))

    def _read_trigram_block(self, stream):
        """Read a block of trigram frequencies."""

        freqs = []

        # Read 20 lines at a time.

        for i in range(20):
            freqs.append(self._get_trigram_weight(stream.readline()))

        return filter(lambda x: x is not None, freqs)

    def freqs(self, fileids=None):
        """Return trigram frequencies for a language from the corpus."""

        return concat([self.CorpusView(path, self._read_trigram_block)
                       for path in self.abspaths(fileids=fileids)])


class LangDetect(object):

    """Detect language in a text."""

    language_trigrams = {}
    langid = LazyCorpusLoader('langid', LangIdCorpusReader, r'(?!\.).*\.txt')

    def __init__(self, languages=['nl', 'en', 'fr', 'de', 'es']):
        for lang in languages:

            self.language_trigrams[lang] = FreqDist()

            for f in self.langid.freqs(fileids=lang + "-3grams.txt"):
                self.language_trigrams[lang].inc(f[0], f[1])

    def detect(self, text):
        """Detect the text's language."""

        words = nltk_word_tokenize(text.lower())
        trigrams = {}
        scores = dict([(lang, 0) for lang in self.language_trigrams.keys()])

        for match in words:

            for trigram in self.get_word_trigrams(match):

                if not trigram in trigrams.keys():
                    trigrams[trigram] = 0

                trigrams[trigram] += 1

        total = sum(trigrams.values())

        for trigram, count in trigrams.items():

            for lang, frequencies in self.language_trigrams.items():

                # Normalize and add to the total score.

                scores[lang] += ((float(frequencies[trigram]) /
                                  float(frequencies.N())) *
                                 (float(count) / float(total)))

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[0][0]

    def get_word_trigrams(self, match):
        return [''.join(trigram)
                for trigram in nltk_trigrams(match) if trigram is not None]


def _get_langdetector():
    """Get an instance of :class:`LangDetect`; but better use the singleton
    returned by :meth:`get_langdetector`."""

    return LangDetect()


get_langdetector = memoize(_get_langdetector)
"""Get a singleton instance of :class:`LangDetect`."""


def _get_stopdetector():
    """Get an instance of :class:`StopwordsDetector`; but better use the
    singleton returned by :meth:`get_langdetector`."""

    return StopwordsDetector()


get_stopdetector = memoize(_get_stopdetector)
"""Get a singleton instance of :class:`StopwordsDetector`."""
