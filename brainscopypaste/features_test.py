from brainscopypaste.features import (_get_pronunciations, _get_aoa,
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


def test_syllables_count():
    assert SubstitutionFeaturesMixin._syllables_count('hello') == 2
    assert SubstitutionFeaturesMixin._syllables_count('mountain') == 2
    assert SubstitutionFeaturesMixin._syllables_count('makakiki') is None


def test_phonemes_count():
    assert SubstitutionFeaturesMixin._phonemes_count('hello') == 4
    assert SubstitutionFeaturesMixin._phonemes_count('mountain') == 6
    assert SubstitutionFeaturesMixin._phonemes_count('makakiki') is None


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
    # So no synonyms, which yields `None`.
    assert SubstitutionFeaturesMixin._synonyms_count('lamp') is None
    # 'makakiki' does not exist.
    assert SubstitutionFeaturesMixin._synonyms_count('makakiki') is None


def test_aoa():
    assert SubstitutionFeaturesMixin._aoa('time') == 5.16
    assert SubstitutionFeaturesMixin._aoa('vocative') == 14.27
    assert SubstitutionFeaturesMixin._aoa('wickiup') is None
