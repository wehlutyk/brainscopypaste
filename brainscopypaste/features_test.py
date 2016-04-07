from os.path import exists
import pickle

import pytest
import numpy as np
from sklearn.decomposition import PCA

from brainscopypaste.db import Quote, Substitution
from brainscopypaste.features import (_get_pronunciations, _get_aoa,
                                      _get_clearpond,
                                      SubstitutionFeaturesMixin)
from brainscopypaste.utils import is_int, unpickle
from brainscopypaste.conf import settings


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


def drop_caches():
    unpickle.drop_cache()
    _get_aoa.drop_cache()
    _get_clearpond.drop_cache()
    _get_pronunciations.drop_cache()
    SubstitutionFeaturesMixin._substitution_features.drop_cache()
    SubstitutionFeaturesMixin._source_destination_features.drop_cache()
    SubstitutionFeaturesMixin.features.drop_cache()
    SubstitutionFeaturesMixin.components.drop_cache()
    SubstitutionFeaturesMixin._average.drop_cache()
    SubstitutionFeaturesMixin.feature_average.drop_cache()
    SubstitutionFeaturesMixin.component_average.drop_cache()
    SubstitutionFeaturesMixin._transformed_feature.drop_cache()
    for feature in SubstitutionFeaturesMixin.__features__:
        getattr(SubstitutionFeaturesMixin, '_' + feature).drop_cache()


def test_syllables_count():
    drop_caches()
    assert SubstitutionFeaturesMixin._syllables_count('hello') == 2
    assert SubstitutionFeaturesMixin._syllables_count('mountain') == 2
    assert np.isnan(SubstitutionFeaturesMixin._syllables_count('makakiki'))


def test_syllables_count_none():
    drop_caches()
    assert SubstitutionFeaturesMixin.\
        _syllables_count() == _get_pronunciations().keys()
    for word in SubstitutionFeaturesMixin._syllables_count():
        assert word.islower()


def test_phonemes_count():
    drop_caches()
    assert SubstitutionFeaturesMixin._phonemes_count('hello') == 4
    assert SubstitutionFeaturesMixin._phonemes_count('mountain') == 6
    assert np.isnan(SubstitutionFeaturesMixin._phonemes_count('makakiki'))


def test_phonemes_count_none():
    drop_caches()
    assert SubstitutionFeaturesMixin.\
        _phonemes_count() == _get_pronunciations().keys()
    for word in SubstitutionFeaturesMixin._phonemes_count():
        assert word.islower()


def test_letters_count():
    drop_caches()
    assert SubstitutionFeaturesMixin._letters_count('hello') == 5
    assert SubstitutionFeaturesMixin._letters_count('mountain') == 8
    assert SubstitutionFeaturesMixin._letters_count('makakiki') == 8


def test_letters_count_none():
    drop_caches()
    with settings.file_override('TOKENS'):
        with open(settings.TOKENS, 'wb') as f:
            pickle.dump({'these', 'are', 'tokens'}, f)
        assert SubstitutionFeaturesMixin.\
            _letters_count() == {'these', 'are', 'tokens'}


@pytest.mark.skipif(not exists(settings.TOKENS),
                    reason='missing computed feature')
def test_letters_count_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._letters_count():
        assert word.islower() or is_int(word[0]) or is_int(word[-1])


def test_synonyms_count():
    drop_caches()
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


def test_synonyms_count_none():
    drop_caches()
    # Lemmas are properly counted.
    assert len(SubstitutionFeaturesMixin._synonyms_count()) == 147306
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._synonyms_count():
        assert word.islower() or is_int(word[0]) or is_int(word[-1])


def test_aoa():
    drop_caches()
    assert SubstitutionFeaturesMixin._aoa('time') == 5.16
    assert SubstitutionFeaturesMixin._aoa('vocative') == 14.27
    assert np.isnan(SubstitutionFeaturesMixin._aoa('wickiup'))


def test_aoa_none():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._aoa():
        assert word.islower()
    # And it's properly computed.
    drop_caches()
    with settings.file_override('AOA'):
        with open(settings.AOA, 'w') as f:
            f.write('Word,Rating.Mean\nhave,2\ntell,3')
        assert set(SubstitutionFeaturesMixin._aoa()) == {'have', 'tell'}


@pytest.mark.skipif(not exists(settings.DEGREE),
                    reason='missing computed feature')
def test_degree():
    drop_caches()
    assert SubstitutionFeaturesMixin._degree('abdomen') == 1 / (10617 - 1)
    assert SubstitutionFeaturesMixin._degree('speaker') == 9 / (10617 - 1)
    assert np.isnan(SubstitutionFeaturesMixin._degree('wickiup'))


def test_degree_none():
    drop_caches()
    with settings.file_override('DEGREE'):
        with open(settings.DEGREE, 'wb') as f:
            pickle.dump({'dog': 2, 'cat': 3}, f)
        assert set(SubstitutionFeaturesMixin._degree()) == {'dog', 'cat'}


@pytest.mark.skipif(not exists(settings.DEGREE),
                    reason='missing computed feature')
def test_degree_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._degree():
        assert (word.islower() or is_int(word[0]) or is_int(word[-1]) or
                word in ['%', '!'])


@pytest.mark.skipif(not exists(settings.PAGERANK),
                    reason='missing computed feature')
def test_pagerank():
    drop_caches()
    assert abs(SubstitutionFeaturesMixin._pagerank('you') -
               0.0006390798677378056) < 1e-15
    assert abs(SubstitutionFeaturesMixin._pagerank('play') -
               0.0012008124120435305) < 1e-15
    assert np.isnan(SubstitutionFeaturesMixin._pagerank('wickiup'))


def test_pagerank_none():
    drop_caches()
    with settings.file_override('PAGERANK'):
        with open(settings.PAGERANK, 'wb') as f:
            pickle.dump({'dog': 2, 'cat': 3}, f)
        assert set(SubstitutionFeaturesMixin._pagerank()) == {'dog', 'cat'}


@pytest.mark.skipif(not exists(settings.PAGERANK),
                    reason='missing computed feature')
def test_pagerank_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._pagerank():
        assert (word.islower() or is_int(word[0]) or is_int(word[-1]) or
                word in ['%', '!'])


@pytest.mark.skipif(not exists(settings.BETWEENNESS),
                    reason='missing computed feature')
def test_betweenness():
    drop_caches()
    assert SubstitutionFeaturesMixin.\
        _betweenness('dog') == 0.0046938277117769605
    assert SubstitutionFeaturesMixin.\
        _betweenness('play') == 0.008277234906313704
    assert np.isnan(SubstitutionFeaturesMixin._betweenness('wickiup'))


def test_betweenness_none():
    drop_caches()
    with settings.file_override('BETWEENNESS'):
        with open(settings.BETWEENNESS, 'wb') as f:
            pickle.dump({'dog': 2, 'cat': 3}, f)
        assert set(SubstitutionFeaturesMixin._betweenness()) == {'dog', 'cat'}


@pytest.mark.skipif(not exists(settings.BETWEENNESS),
                    reason='missing computed feature')
def test_betweenness_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._betweenness():
        assert (word.islower() or is_int(word[0]) or is_int(word[-1]) or
                word in ['%', '!'])


@pytest.mark.skipif(not exists(settings.CLUSTERING),
                    reason='missing computed feature')
def test_clustering():
    drop_caches()
    assert abs(SubstitutionFeaturesMixin.
               _clustering('dog') - 0.0009318641757868838) < 1e-17
    assert abs(SubstitutionFeaturesMixin.
               _clustering('play') - 0.0016238663632016216) < 1e-17
    assert np.isnan(SubstitutionFeaturesMixin._clustering('wickiup'))


def test_clustering_none():
    drop_caches()
    with settings.file_override('CLUSTERING'):
        with open(settings.CLUSTERING, 'wb') as f:
            pickle.dump({'dog': 2, 'cat': 3}, f)
        assert set(SubstitutionFeaturesMixin._clustering()) == {'dog', 'cat'}


@pytest.mark.skipif(not exists(settings.CLUSTERING),
                    reason='missing computed feature')
def test_clustering_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._clustering():
        assert (word.islower() or is_int(word[0]) or is_int(word[-1]) or
                word in ['%', '!'])


@pytest.mark.skipif(not exists(settings.FREQUENCY),
                    reason='missing computed feature')
def test_frequency():
    drop_caches()
    assert SubstitutionFeaturesMixin._frequency('dog') == 7865
    assert SubstitutionFeaturesMixin._frequency('play') == 45848
    assert np.isnan(SubstitutionFeaturesMixin._frequency('wickiup'))


def test_frequency_none():
    drop_caches()
    with settings.file_override('FREQUENCY'):
        with open(settings.FREQUENCY, 'wb') as f:
            pickle.dump({'dog': 2, 'cat': 3}, f)
        assert set(SubstitutionFeaturesMixin._frequency()) == {'dog', 'cat'}


@pytest.mark.skipif(not exists(settings.FREQUENCY),
                    reason='missing computed feature')
def test_frequency_none_with_computed():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._frequency():
        assert (word.islower() or is_int(word[0]) or is_int(word[-1]) or
                word in ['%', '!'])


def test_phonological_density():
    drop_caches()
    assert SubstitutionFeaturesMixin._phonological_density('time') == 29
    assert np.isnan(SubstitutionFeaturesMixin._phonological_density('wickiup'))


def test_phonological_density_none():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._phonological_density():
        assert word.islower()
    # And it's computed right.
    drop_caches()
    with settings.file_override('CLEARPOND'):
        with open(settings.CLEARPOND, 'w') as f:
            f.write('dog' + 5 * '\t' + '2' + 24 * '\t' + '3\n'
                    'cat' + 5 * '\t' + '2' + 24 * '\t' + '3')
        assert set(SubstitutionFeaturesMixin.
                   _phonological_density()) == {'dog', 'cat'}


def test_orthographical_density():
    drop_caches()
    assert SubstitutionFeaturesMixin._orthographical_density('time') == 13
    assert np.isnan(SubstitutionFeaturesMixin.
                    _orthographical_density('wickiup'))


def test_orthographical_density_none():
    drop_caches()
    # Lemmas are all lowercase.
    for word in SubstitutionFeaturesMixin._orthographical_density():
        assert word.islower()
    # And it's computed right.
    drop_caches()
    with settings.file_override('CLEARPOND'):
        with open(settings.CLEARPOND, 'w') as f:
            f.write('dog' + 5 * '\t' + '2' + 24 * '\t' + '3\n'
                    'cat' + 5 * '\t' + '2' + 24 * '\t' + '3')
        assert set(SubstitutionFeaturesMixin.
                   _orthographical_density()) == {'dog', 'cat'}


@pytest.fixture
def normal_substitution():
    q1 = Quote(string='Oh yes it is the containing part')
    q2 = Quote(string='It is the other part')
    return Substitution(source=q1, destination=q2, start=2, position=3)


def test_substitution_features(normal_substitution):
    drop_caches()
    # A shortcut.
    s = normal_substitution

    # Check we defined the right substitution.
    assert s.tokens == ('containing', 'other')
    assert s.lemmas == ('contain', 'other')

    # An unknown feature raises an error
    with pytest.raises(ValueError):
        s._substitution_features('unknown_feature')

    # Syllable, phonemes, letters counts, and densities are right,
    # and computed on tokens.
    assert s._substitution_features('syllables_count') == (3, 2)
    assert s._substitution_features('phonemes_count') == (8, 3)
    assert s._substitution_features('letters_count') == (10, 5)
    assert np.isnan(s._substitution_features('phonological_density')[0])
    assert s._substitution_features('phonological_density')[1] == np.log(7)
    assert np.isnan(s._substitution_features('orthographical_density')[0])
    assert s._substitution_features('orthographical_density')[1] == np.log(5)

    # Synonyms count and age-of-acquisition are right, and computed on lemmas.
    # The rest of the features need computed files, and are only tested through
    # 'features()' directly so as not to make other file-dependent tests heavy
    # to read.
    assert s._substitution_features('synonyms_count') == \
        (np.log(3), np.log(.5))
    assert s._substitution_features('aoa') == (7.88, 5.33)

    # Unknown words are ignored. Also when in the rest of the sentence.
    q1 = Quote(string='makakiki is the goal')
    q2 = Quote(string='makakiki is the moukakaka')
    s = Substitution(source=q1, destination=q2, start=0, position=3)
    assert s._substitution_features('syllables_count')[0] == 1
    # np.nan != np.nan so we can't `assert s.features(...) == (1, np.nan)`
    assert np.isnan(s._substitution_features('syllables_count')[1])


def test_source_destination_features(normal_substitution):
    drop_caches()
    # A shortcut.
    s = normal_substitution

    # Check we defined the right substitution.
    assert s.tokens == ('containing', 'other')
    assert s.lemmas == ('contain', 'other')

    # An unknown feature raises an error
    with pytest.raises(ValueError):
        s._source_destination_features('unknown_feature')

    # Syllable, phonemes, letters counts, and densities are right,
    # and computed on tokens.
    assert (s._source_destination_features('syllables_count')[0] ==
            [1, 1, 1, 3, 1]).all()
    assert (s._source_destination_features('syllables_count')[1] ==
            [1, 1, 1, 2, 1]).all()
    assert (s._source_destination_features('phonemes_count')[0] ==
            [2, 2, 2, 8, 4]).all()
    assert (s._source_destination_features('phonemes_count')[1] ==
            [2, 2, 2, 3, 4]).all()
    assert (s._source_destination_features('letters_count')[0] ==
            [2, 2, 3, 10, 4]).all()
    assert (s._source_destination_features('letters_count')[1] ==
            [2, 2, 3, 5, 4]).all()
    sf, df = s._source_destination_features('phonological_density')
    assert (sf[np.isfinite(sf)] == np.log([31, 24, 9, 28])).all()
    assert (np.isnan(sf) == [False, False, False, True, False]).all()
    assert (df == np.log([31, 24, 9, 7, 28])).all()
    sf, df = s._source_destination_features('orthographical_density')
    assert (sf[np.isfinite(sf)] == np.log([17, 14, 11, 20])).all()
    assert (np.isnan(sf) == [False, False, False, True, False]).all()
    assert (df == np.log([17, 14, 11, 5, 20])).all()

    # Synonyms count and age-of-acquisition are right, and computed on lemmas.
    # The rest of the features need computed files, and are only tested through
    # 'features()' directly so as not to make other file-dependent tests heavy
    # to read.
    sf, df = s._source_destination_features('synonyms_count')
    assert (sf[np.isfinite(sf)] ==
            np.log([1, 1, 3, 2.4444444444444446])).all()
    assert (np.isnan(sf) == [False, False, True, False, False]).all()
    assert (df[np.isfinite(df)] ==
            np.log([1, 1, .5, 2.4444444444444446])).all()
    assert (np.isnan(df) == [False, False, True, False, False]).all()
    sf, df = s._source_destination_features('aoa')
    assert (sf[np.isfinite(sf)] == [5.11, 7.88, 5.11]).all()
    assert (np.isnan(sf) == [True, False, True, False, False]).all()
    assert (df[np.isfinite(df)] == [5.11, 5.33, 5.11]).all()
    assert (np.isnan(df) == [True, False, True, False, False]).all()


def test_features(normal_substitution):
    drop_caches()
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
    assert np.isnan(s.features('phonological_density')[0])
    assert s.features('phonological_density')[1] == np.log(7)
    assert np.isnan(s.features('orthographical_density')[0])
    assert s.features('orthographical_density')[1] == np.log(5)
    # Same with features computed relative to sentence.
    assert s.features('syllables_count',
                      sentence_relative=True) == (3 - 7/5, 2 - 6/5)
    assert s.features('phonemes_count',
                      sentence_relative=True) == (8 - 18/5, 3 - 13/5)
    assert s.features('letters_count',
                      sentence_relative=True) == (10 - 21/5, 5 - 16/5)
    assert np.isnan(s.features('phonological_density',
                               sentence_relative=True)[0])
    assert s.features('phonological_density',
                      sentence_relative=True)[1] == \
        np.log(7) - np.log([31, 24, 9, 7, 28]).mean()
    assert np.isnan(s.features('orthographical_density',
                               sentence_relative=True)[0])
    assert s.features('orthographical_density',
                      sentence_relative=True)[1] == \
        np.log(5) - np.log([17, 14, 11, 5, 20]).mean()

    # Synonyms count and age-of-acquisition are right, and computed on lemmas.
    # The rest of the features need computed files, and are tested separately.
    assert s.features('synonyms_count') == (np.log(3), np.log(.5))
    assert s.features('aoa') == (7.88, 5.33)
    # Same with features computed relative to sentence.
    assert s.features('synonyms_count', sentence_relative=True) == \
        (np.log(3) - np.log([1, 1, 3, 2.4444444444444446]).mean(),
         np.log(.5) - np.log([1, 1, .5, 2.4444444444444446]).mean())
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


@pytest.mark.skipif(not exists(settings.DEGREE),
                    reason='missing computed feature')
def test_features_degree(normal_substitution):
    drop_caches()
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert s.features('degree') == \
        (np.log(9.419743782969103e-05), np.log(0.0008477769404672192))
    # Same with features computed relative to sentence.
    assert s.features('degree', sentence_relative=True) == \
        (np.log(9.419743782969103e-05) - (-7.3658186158894221),
         np.log(0.0008477769404672192) - (-6.9263737004221797))


@pytest.mark.skipif(not exists(settings.PAGERANK),
                    reason='missing computed feature')
def test_features_pagerank(normal_substitution):
    drop_caches()
    s = normal_substitution
    # Values are right, and computed on lemmas.
    # (We use np.exp instead of np.log to avoid translating the uncertainty
    # tolerance.)
    assert abs(np.exp(s.features('pagerank')[0]) -
               2.9236183726513393e-05) < 1e-15
    assert abs(np.exp(s.features('pagerank')[1]) -
               6.421655879054584e-05) < 1e-15
    # Same with features computed relative to sentence.
    assert abs(np.exp(s.features('pagerank', sentence_relative=True)[0]) -
               (2.9236183726513393e-05 / 7.4667929803002613e-05)) < 1e-15
    assert abs(np.exp(s.features('pagerank', sentence_relative=True)[1]) -
               (6.421655879054584e-05 / 8.739354974404687e-05)) < 1e-15


@pytest.mark.skipif(not exists(settings.BETWEENNESS),
                    reason='missing computed feature')
def test_features_betweenness(normal_substitution):
    drop_caches()
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert np.isnan(s.features('betweenness')[0])
    assert s.features('betweenness')[1] == np.log(0.0003369277738594168)
    # Same with features computed relative to sentence.
    assert np.isnan(s.features('betweenness',
                               sentence_relative=True)[0])
    assert s.features('betweenness', sentence_relative=True)[1] == \
        np.log(0.0003369277738594168) - (-7.3319337537445257)


@pytest.mark.skipif(not exists(settings.CLUSTERING),
                    reason='missing computed feature')
def test_features_clustering(normal_substitution):
    drop_caches()
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert np.isnan(s.features('clustering')[0])
    assert s.features('clustering')[1] == np.log(0.0037154495910700605)
    # Same with features computed relative to sentence.
    assert np.isnan(s.features('clustering', sentence_relative=True)[0])
    assert s.features('clustering', sentence_relative=True)[1] == \
        np.log(0.0037154495910700605) - (-6.2647504887460004)


@pytest.mark.skipif(not exists(settings.FREQUENCY),
                    reason='missing computed feature')
def test_features_frequency(normal_substitution):
    drop_caches()
    s = normal_substitution
    # Values are right, and computed on lemmas.
    assert s.features('frequency') == (np.log(3992), np.log(81603))
    # Same with features computed relative to sentence.
    assert s.features('frequency', sentence_relative=True) == \
        (np.log(3992) - 12.447170233839325, np.log(81603) - 13.050684967349508)


def test_transformed_feature():
    # Phonological density is log-transformed.
    drop_caches()
    transformed_phonological_density = SubstitutionFeaturesMixin.\
        _transformed_feature('phonological_density')
    assert transformed_phonological_density('time') == np.log(29)
    assert np.isnan(transformed_phonological_density('wickiup'))
    # Doc and name are transformed too.
    assert transformed_phonological_density.__doc__ == \
        'log(' + SubstitutionFeaturesMixin._phonological_density.__doc__ + ')'
    assert transformed_phonological_density.__name__ == \
        '_log_phonological_density'
    # And the list of words is properly computed.
    drop_caches()
    with settings.file_override('CLEARPOND'):
        with open(settings.CLEARPOND, 'w') as f:
            f.write('dog' + 5 * '\t' + '2' + 24 * '\t' + '3\n'
                    'cat' + 5 * '\t' + '2' + 24 * '\t' + '3')
        assert set(transformed_phonological_density()) == {'dog', 'cat'}

    # AoA is left untouched.
    drop_caches()
    transformed_aoa = SubstitutionFeaturesMixin._transformed_feature('aoa')
    assert transformed_aoa('time') == 5.16
    assert transformed_aoa('vocative') == 14.27
    assert np.isnan(transformed_aoa('wickiup'))
    # Doc and name are passed on.
    assert transformed_aoa.__doc__ == SubstitutionFeaturesMixin._aoa.__doc__
    assert transformed_aoa.__name__ == '_aoa'
    # And the list of words is properly computed.
    drop_caches()
    with settings.file_override('AOA'):
        with open(settings.AOA, 'w') as f:
            f.write('Word,Rating.Mean\nhave,2\ntell,3')
        assert set(transformed_aoa()) == {'have', 'tell'}


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


def test_average():
    drop_caches()

    # Our test feature.
    values = {'dog': 2, 'hound': 3, 'frisbee': 4, 'chase': 6, 'cad': 7,
              'other': 8}

    def feature(word=None):
        if word is None:
            return set(values.keys())
        else:
            return values.get(word, np.nan)

    # Global average and average of synonyms are well retrieved.
    assert SubstitutionFeaturesMixin._average(feature, None) == 30 / 6
    assert SubstitutionFeaturesMixin._average(feature, (2, 5)) == \
        (16 / 3 + 9 / 2) / 2

    # If we have a lot of NaNs, things still work well.
    drop_caches()
    values = {'dog': 2, 'screen': 3, 'frisbee': 4, 'chase': np.nan, 'cad': 7,
              'other': 8, 'blind': np.nan, 'cover': np.nan}
    assert SubstitutionFeaturesMixin._average(feature, None) == 24 / 5
    # 'frisbee' has no synonyms. All the synonyms of 'screen' are np.nan.
    assert SubstitutionFeaturesMixin._average(feature, (2, 5)) == 7


def test_feature_average():
    # Test a non-transformed feature (AoA).
    drop_caches()
    with settings.file_override('AOA'):
        with open(settings.AOA, 'w') as f:
            f.write('Word,Rating.Mean\n'
                    'dog,2\nhound,3\nfrisbee,4\nchase,6\ncad,7\nother,8')
        assert SubstitutionFeaturesMixin.feature_average('aoa') == 30 / 6
        assert SubstitutionFeaturesMixin.\
            feature_average('aoa', synonyms_from_range=(2, 5)) == \
            (16 / 3 + 9 / 2) / 2
    # Test a log-transformed feature (phonological density).
    drop_caches()
    with settings.file_override('CLEARPOND'):
        with open(settings.CLEARPOND, 'w') as f:
            f.write('dog' + 5 * '\t' + '0' + 24 * '\t' + '2\n'
                    'hound' + 5 * '\t' + '0' + 24 * '\t' + '3\n'
                    'frisbee' + 5 * '\t' + '0' + 24 * '\t' + '4\n'
                    'chase' + 5 * '\t' + '0' + 24 * '\t' + '6\n'
                    'cad' + 5 * '\t' + '0' + 24 * '\t' + '7\n'
                    'other' + 5 * '\t' + '0' + 24 * '\t' + '8')
        assert SubstitutionFeaturesMixin.\
            feature_average('phonological_density') == \
            np.log([2, 3, 4, 6, 7, 8]).mean()
        assert SubstitutionFeaturesMixin.\
            feature_average('phonological_density',
                            synonyms_from_range=(np.log(2), np.log(5))) == \
            (np.log([3, 6, 7]).mean() + np.log([2, 7]).mean()) / 2
    # _synonyms_count(word=None) returns a list of words, some of which have
    # a _synonyms_count(word) == np.nan (because 0 synonyms is returned as
    # np.nan). So check that synonyms_count feature average is not np.nan.
    assert np.isfinite(SubstitutionFeaturesMixin
                       .feature_average('synonyms_count'))


def test_components(normal_substitution):
    drop_caches()
    # A shortcut.
    s = normal_substitution

    # Create a test PCA with features alternatively log-transformed and not,
    # alternatively on tokens and lemmas.
    features = ('letters_count', 'aoa', 'synonyms_count',
                'phonological_density')
    pca = PCA(n_components=3)

    # Trying this with a PCA fitted with the wrong shape fails.
    pca.fit(np.array([[1, 1, 0], [0, 1, 0], [0, 1, 1]]))
    with pytest.raises(AssertionError):
        s.components(0, pca, features)
    with pytest.raises(AssertionError):
        s.components(0, pca, features, sentence_relative=True)
    # Trying this with unknown features fails.
    with pytest.raises(ValueError) as excinfo:
        s.components(0, pca, ('letters_count', 'unknown_feature', 'aoa'))
    assert 'Unknown feature' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        s.components(0, pca, ('letters_count', 'unknown_feature', 'aoa'),
                     sentence_relative=True)
    assert 'Unknown feature' in str(excinfo.value)

    # Now training with the right shape, we get the expected hand-computed
    # values.
    pca.fit(np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]]))
    sign = np.sign(pca.components_[0, 0])
    assert np.isnan(s.components(0, pca, features)[0])
    assert abs(sign * s.components(0, pca, features)[1] -
               4.5386185157523178) < 1e-14
    assert np.isnan(s.components(1, pca, features)[0])
    assert abs(sign * s.components(1, pca, features)[1] -
               1.4878619981409629) < 1e-14
    assert np.isnan(s.components(2, pca, features)[0])
    assert abs(sign * s.components(2, pca, features)[1] -
               2.5067990036967074) < 1e-14

    # Also for sentence_relative=True.
    assert np.isnan(s.components(0, pca, features, sentence_relative=True)[0])
    assert abs(sign * s.components(0, pca, features,
                                   sentence_relative=True)[1] -
               (4.5386185157523178 - 2.9821934691598986)) < 1e-14
    assert np.isnan(s.components(1, pca, features, sentence_relative=True)[0])
    assert abs(sign * s.components(1, pca, features,
                                   sentence_relative=True)[1] -
               (1.4878619981409629 - 0.95091629901938557)) < 1e-14
    assert np.isnan(s.components(2, pca, features, sentence_relative=True)[0])
    assert abs(sign * s.components(2, pca, features,
                                   sentence_relative=True)[1] -
               (2.5067990036967074 - 3.1573434812204084)) < 1e-14


def test_component_average():
    drop_caches()

    # Create a test PCA that will use features we later override.
    features = ('aoa', 'phonological_density')
    pca = PCA(n_components=2)

    # Trying this with a PCA fitted with the wrong shape fails.
    pca.fit(np.array([[1, 1, 0], [0, 1, 0], [0, 1, 1]]))
    with pytest.raises(AssertionError):
        SubstitutionFeaturesMixin.component_average(0, pca, features)
    with pytest.raises(AssertionError):
        SubstitutionFeaturesMixin.component_average(0, pca, features,
                                                    synonyms_from_range=(2, 5))
    # Trying this with unknown features fails.
    with pytest.raises(ValueError) as excinfo:
        SubstitutionFeaturesMixin.component_average(
            0, pca, ('letters_count', 'unknown_feature', 'aoa'))
    assert 'Unknown feature' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        SubstitutionFeaturesMixin.component_average(
            0, pca, ('letters_count', 'unknown_feature', 'aoa'),
            synonyms_from_range=(2, 5))
    assert 'Unknown feature' in str(excinfo.value)

    # Now with features we override to test manual values.
    drop_caches()
    pca.fit(np.array([[2, 1], [1, -2]]))
    sign = np.sign(pca.components_[0, 0])
    with settings.file_override('AOA', 'CLEARPOND'):
        with open(settings.AOA, 'w') as f:
            f.write('Word,Rating.Mean\n'
                    'dog,2\nhound,3\nfrisbee,4\nchase,6\ncad,7\nother,8')
        with open(settings.CLEARPOND, 'w') as f:
            f.write('dog' + 5 * '\t' + '0' + 24 * '\t' + '2\n'
                    'hound' + 5 * '\t' + '0' + 24 * '\t' + '3\n'
                    'frisbee' + 5 * '\t' + '0' + 24 * '\t' + '4\n'
                    'screen' + 5 * '\t' + '0' + 24 * '\t' + '5\n'
                    'chase' + 5 * '\t' + '0' + 24 * '\t' + '6\n'
                    'other' + 5 * '\t' + '0' + 24 * '\t' + '8')

        # We find the hand-computed values alright.
        assert abs(sign * SubstitutionFeaturesMixin
                   .component_average(0, pca, features) -
                   2.7921497899976822) < 1e-14
        assert abs(sign * SubstitutionFeaturesMixin
                   .component_average(1, pca, features) -
                   2.3369703188414315) < 1e-14
        # Same with synonyms_from_range.
        assert abs(sign * SubstitutionFeaturesMixin
                   .component_average(0, pca, features,
                                      synonyms_from_range=(-3, -1)) -
                   2.0420406691669841) < 1e-14
        assert abs(sign * SubstitutionFeaturesMixin
                   .component_average(1, pca, features,
                                      synonyms_from_range=(-2, 0)) -
                   1.1639817453758932) < 1e-14
