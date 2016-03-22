import pytest
import numpy as np

from brainscopypaste.db import Quote, Substitution
from brainscopypaste.features import (_get_pronunciations, _get_aoa,
                                      _get_clearpond,
                                      SubstitutionFeaturesMixin)


def test_get_pronunciations():
    pronunciations = _get_pronunciations()
    # We have the right kind of data.
    assert pronunciations['hello'] == [['HH', 'AH0', 'L', 'OW1'],
                                       ['HH', 'EH0', 'L', 'OW1']]
    # And what's loaded is memoized.
    assert pronunciations is _get_pronunciations()


def test_get_aoa():
    aoa = _get_aoa()
    # We have the right kind of data.
    assert aoa['time'] == 5.16
    # 'NA' terms were not loaded.
    assert 'wickiup' not in aoa
    assert len(aoa) == 30102
    # And what's loaded is memoized.
    assert aoa is _get_aoa()


def test_get_clearpond():
    clearpond = _get_clearpond()
    # We have the right kind of data.
    assert clearpond['phonological']['dog'] == 25
    assert clearpond['phonological']['cat'] == 50
    assert clearpond['phonological']['ghost'] == 14
    assert clearpond['phonological']['you'] == 49
    assert clearpond['orthographical']['dog'] == 20
    assert clearpond['orthographical']['cat'] == 33
    assert clearpond['orthographical']['ghost'] == 2
    assert clearpond['orthographical']['you'] == 4
    # And what's loaded is memoized.
    assert clearpond is _get_clearpond()


def test_syllables_count():
    assert SubstitutionFeaturesMixin._syllables_count('hello') == 2
    assert SubstitutionFeaturesMixin._syllables_count('mountain') == 2
    assert SubstitutionFeaturesMixin._syllables_count('makakiki') is np.nan


def test_phonemes_count():
    assert SubstitutionFeaturesMixin._phonemes_count('hello') == 4
    assert SubstitutionFeaturesMixin._phonemes_count('mountain') == 6
    assert SubstitutionFeaturesMixin._phonemes_count('makakiki') is np.nan


def test_letters_count():
    assert SubstitutionFeaturesMixin._letters_count('hello') == 5
    assert SubstitutionFeaturesMixin._letters_count('mountain') == 8
    assert SubstitutionFeaturesMixin._letters_count('makakiki') == 8


def test_synonyms_count():
    # 'hello' has a single synset, with 5 members. So 4 synonyms.
    assert SubstitutionFeaturesMixin._synonyms_count('hello') == 4
    # 'mountain' has two synsets, with 2 and 27 members.
    # So ((2-1) + (27-1))/2 synonyms.
    assert SubstitutionFeaturesMixin._synonyms_count('mountain') == 13.5
    # 'lamp' has two synsets, with only one member in each.
    # So no synonyms, which yields `np.nan`.
    assert SubstitutionFeaturesMixin._synonyms_count('lamp') is np.nan
    # 'makakiki' does not exist.
    assert SubstitutionFeaturesMixin._synonyms_count('makakiki') is np.nan


def test_aoa():
    assert SubstitutionFeaturesMixin._aoa('time') == 5.16
    assert SubstitutionFeaturesMixin._aoa('vocative') == 14.27
    assert SubstitutionFeaturesMixin._aoa('wickiup') is np.nan


def test_phonological_density():
    assert SubstitutionFeaturesMixin._phonological_density('time') == 29
    assert SubstitutionFeaturesMixin.\
        _phonological_density('wickiup') is np.nan


def test_orthographical_density():
    assert SubstitutionFeaturesMixin._orthographical_density('time') == 13
    assert SubstitutionFeaturesMixin.\
        _orthographical_density('wickiup') is np.nan


def test_features():
    q1 = Quote(string='It is the containing part')
    q2 = Quote(string='It is the other part')
    s = Substitution(source=q1, destination=q2, start=0, position=3)
    # Check we defined the right substitution.
    assert s.tokens == ('containing', 'other')
    assert s.lemmas == ('contain', 'other')

    # An unknown feature raises an error
    with pytest.raises(ValueError):
        s.features('unknown_feature')
    with pytest.raises(ValueError):
        s.features('unknown_feature', sentence_relative=True)

    # Syllable, phonemes, letters counts, and densities are right,
    # and computed on tokens.
    assert s.features('syllables_count') == (3, 2)
    assert s.features('phonemes_count') == (8, 3)
    assert s.features('letters_count') == (10, 5)
    assert s.features('phonological_density') == (0, 7)
    assert s.features('orthographical_density') == (0, 5)
    assert s.features('syllables_count',
                      sentence_relative=True) == (3 - 7/5, 2 - 6/5)
    assert s.features('phonemes_count',
                      sentence_relative=True) == (8 - 18/5, 3 - 13/5)
    assert s.features('letters_count',
                      sentence_relative=True) == (10 - 21/5, 5 - 16/5)
    assert s.features('phonological_density',
                      sentence_relative=True) == (0 - 92/5, 7 - 99/5)
    assert s.features('orthographical_density',
                      sentence_relative=True) == (0 - 62/5, 5 - 67/5)

    # Unknown words are ignored. Also when in the rest of the sentence.
    q1 = Quote(string='makakiki is the goal')
    q2 = Quote(string='makakiki is the moukakaka')
    s = Substitution(source=q1, destination=q2, start=0, position=3)
    assert s.features('syllables_count')[0] == 1
    # np.nan != np.nan so we can't `assert s.features(...) == (1, np.nan)`
    assert np.isnan(s.features('syllables_count')[1])
    assert s.features('syllables_count', sentence_relative=True)[0] == 1 - 3/3
    assert np.isnan(s.features('syllables_count', sentence_relative=True)[1])
