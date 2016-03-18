from brainscopypaste.features import _get_pronunciations, _get_aoa


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
