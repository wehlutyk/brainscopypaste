from os.path import exists

import pytest
import numpy as np

from brainscopypaste.db import Quote, Substitution
from brainscopypaste.features import (_get_pronunciations, _get_aoa,
                                      _get_clearpond,
                                      SubstitutionFeaturesMixin)
from brainscopypaste.paths import (fa_norms_degrees_pickle,
                                   fa_norms_PR_scores_pickle,
                                   fa_norms_BCs_pickle, fa_norms_CCs_pickle,
                                   mt_frequencies_pickle)
from brainscopypaste.utils import is_int


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
    assert np.isnan(SubstitutionFeaturesMixin._syllables_count('makakiki'))
    assert SubstitutionFeaturesMixin.\
        _syllables_count() == _get_pronunciations().keys()
    for word in SubstitutionFeaturesMixin._syllables_count():
        assert word.islower()


def test_phonemes_count():
    assert SubstitutionFeaturesMixin._phonemes_count('hello') == 4
    assert SubstitutionFeaturesMixin._phonemes_count('mountain') == 6
    assert np.isnan(SubstitutionFeaturesMixin._phonemes_count('makakiki'))
    assert SubstitutionFeaturesMixin.\
        _phonemes_count() == _get_pronunciations().keys()
    for word in SubstitutionFeaturesMixin._phonemes_count():
        assert word.islower()


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
    assert np.isnan(SubstitutionFeaturesMixin._synonyms_count('lamp'))
    # 'makakiki' does not exist.
    assert np.isnan(SubstitutionFeaturesMixin._synonyms_count('makakiki'))
    # Lemmas are properly counted.
    assert len(SubstitutionFeaturesMixin._synonyms_count()) == 147306
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._synonyms_count():
        assert word.islower() or is_int(word[0]) or is_int(word[-1])


def test_aoa():
    assert SubstitutionFeaturesMixin._aoa('time') == 5.16
    assert SubstitutionFeaturesMixin._aoa('vocative') == 14.27
    assert np.isnan(SubstitutionFeaturesMixin._aoa('wickiup'))


@pytest.mark.skipif(not exists(fa_norms_degrees_pickle),
                    reason='missing computed feature')
def test_fa_degree():
    assert SubstitutionFeaturesMixin._fa_degree('abdomen') == 1 / (10617 - 1)
    assert SubstitutionFeaturesMixin._fa_degree('speaker') == 9 / (10617 - 1)
    assert np.isnan(SubstitutionFeaturesMixin._fa_degree('wickiup'))


@pytest.mark.skipif(not exists(fa_norms_PR_scores_pickle),
                    reason='missing computed feature')
def test_fa_pagerank():
    assert abs(SubstitutionFeaturesMixin._fa_pagerank('you') -
               0.0006390798677378056) < 1e-15
    assert abs(SubstitutionFeaturesMixin._fa_pagerank('play') -
               0.0012008124120435305) < 1e-15
    assert np.isnan(SubstitutionFeaturesMixin._fa_pagerank('wickiup'))


@pytest.mark.skipif(not exists(fa_norms_BCs_pickle),
                    reason='missing computed feature')
def test_fa_betweenness():
    assert SubstitutionFeaturesMixin.\
        _fa_betweenness('dog') == 0.0046938277117769605
    assert SubstitutionFeaturesMixin.\
        _fa_betweenness('play') == 0.008277234906313704
    assert np.isnan(SubstitutionFeaturesMixin._fa_betweenness('wickiup'))


@pytest.mark.skipif(not exists(fa_norms_CCs_pickle),
                    reason='missing computed feature')
def test_fa_clustering():
    assert SubstitutionFeaturesMixin.\
        _fa_clustering('dog') == 0.0009318641757868838
    assert SubstitutionFeaturesMixin.\
        _fa_clustering('play') == 0.0016238663632016216
    assert np.isnan(SubstitutionFeaturesMixin._fa_clustering('wickiup'))


@pytest.mark.skipif(not exists(mt_frequencies_pickle),
                    reason='missing computed feature')
def test_frequency():
    assert SubstitutionFeaturesMixin._frequency('dog') == 7865
    assert SubstitutionFeaturesMixin._frequency('play') == 45848
    assert np.isnan(SubstitutionFeaturesMixin._frequency('wickiup'))


def test_phonological_density():
    assert SubstitutionFeaturesMixin._phonological_density('time') == 29
    assert np.isnan(SubstitutionFeaturesMixin._phonological_density('wickiup'))


def test_orthographical_density():
    assert SubstitutionFeaturesMixin._orthographical_density('time') == 13
    assert np.isnan(SubstitutionFeaturesMixin.
                    _orthographical_density('wickiup'))


@pytest.fixture
def normal_substitution():
    q1 = Quote(string='It is the containing part')
    q2 = Quote(string='It is the other part')
    return Substitution(source=q1, destination=q2, start=0, position=3)


def test_features(normal_substitution):
    # A shortcut.
    s = normal_substitution

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
    # Same with features computed relative to sentence.
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

    # Synonyms count and age-of-acquisition are right, and computed on lemmas.
    # (the rest of the features need computed files,
    # and are tested separately).
    assert s.features('synonyms_count') == (3, .5)
    assert s.features('aoa') == (7.88, 5.33)
    # Same with features computed relative to sentence.
    assert s.features('synonyms_count', sentence_relative=True) == \
        (3 - 1.8611111111111112, .5 - 1.2361111111111112)
    assert s.features('aoa', sentence_relative=True) == \
        (7.88 - 6.033333333333334, 5.33 - 5.183333333333334)

    # Unknown words are ignored. Also when in the rest of the sentence.
    q1 = Quote(string='makakiki is the goal')
    q2 = Quote(string='makakiki is the moukakaka')
    s = Substitution(source=q1, destination=q2, start=0, position=3)
    assert s.features('syllables_count')[0] == 1
    # np.nan != np.nan so we can't `assert s.features(...) == (1, np.nan)`
    assert np.isnan(s.features('syllables_count')[1])
    assert s.features('syllables_count', sentence_relative=True)[0] == 1 - 3/3
    assert np.isnan(s.features('syllables_count', sentence_relative=True)[1])


@pytest.mark.skipif(not exists(fa_norms_degrees_pickle),
                    reason='missing computed feature')
def test_features_fa_degree(normal_substitution):
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert s.features('fa_degree') == \
        (9.419743782969103e-05, 0.0008477769404672192)
    # Same with features computed relative to sentence.
    assert s.features('fa_degree', sentence_relative=True) == \
        (9.419743782969103e-05 - 0.0010550113036925397,
         0.0008477769404672192 - 0.0012057272042200451)


@pytest.mark.skipif(not exists(fa_norms_PR_scores_pickle),
                    reason='missing computed feature')
def test_features_fa_pagerank(normal_substitution):
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert abs(s.features('fa_pagerank')[0] -
               2.9236183726513393e-05) < 1e-15
    assert abs(s.features('fa_pagerank')[1] -
               6.421655879054584e-05) < 1e-15
    # Same with features computed relative to sentence.
    assert abs(s.features('fa_pagerank', sentence_relative=True)[0] -
               (2.9236183726513393e-05 - 9.2820794154173557e-05)) < 1e-15
    assert abs(s.features('fa_pagerank', sentence_relative=True)[1] -
               (6.421655879054584e-05 - 9.9816869166980042e-05)) < 1e-15


@pytest.mark.skipif(not exists(fa_norms_BCs_pickle),
                    reason='missing computed feature')
def test_features_fa_betweenness(normal_substitution):
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert np.isnan(s.features('fa_betweenness')[0])
    assert s.features('fa_betweenness')[1] == 0.0003369277738594168
    # Same with features computed relative to sentence.
    assert np.isnan(s.features('fa_betweenness',
                               sentence_relative=True)[0])
    assert s.features('fa_betweenness', sentence_relative=True)[1] == \
        0.0003369277738594168 - 0.00081995401378403285


@pytest.mark.skipif(not exists(fa_norms_CCs_pickle),
                    reason='missing computed feature')
def test_features_fa_clustering(normal_substitution):
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert np.isnan(s.features('fa_clustering')[0])
    assert s.features('fa_clustering')[1] == 0.0037154495910700605
    # Same with features computed relative to sentence.
    assert np.isnan(s.features('fa_clustering', sentence_relative=True)[0])
    assert s.features('fa_clustering', sentence_relative=True)[1] == \
        0.0037154495910700605 - 0.0021628891370054143


@pytest.mark.skipif(not exists(mt_frequencies_pickle),
                    reason='missing computed feature')
def test_features_frequency(normal_substitution):
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert s.features('frequency') == (3992, 81603)
    # Same with features computed relative to sentence.
    assert s.features('frequency', sentence_relative=True) == \
        (3992 - 1373885.6000000001, 81603 - 1389407.8)


def test_strict_synonyms():
    assert SubstitutionFeaturesMixin._strict_synonyms('frisbee') == set()
    assert SubstitutionFeaturesMixin.\
        _strict_synonyms('dog') == {'domestic_dog', 'canis_familiaris',
                                    'frump', 'cad', 'bounder', 'blackguard',
                                    'hound', 'heel', 'frank', 'frankfurter',
                                    'hotdog', 'hot_dog', 'wiener',
                                    'wienerwurst', 'weenie', 'pawl', 'detent',
                                    'click', 'andiron', 'firedog', 'dog-iron',
                                    'chase', 'chase_after', 'trail', 'tail',
                                    'tag', 'give_chase', 'go_after', 'track'}
    assert SubstitutionFeaturesMixin._strict_synonyms('makakiki') == set()
