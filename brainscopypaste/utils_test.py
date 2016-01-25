from brainscopypaste.utils import grouper, grouper_adaptive, langdetect


def test_langdetect():
    assert langdetect('') is None
    assert langdetect('Dear sir, please open the door') == 'en'


def test_grouper():
    base = range(13)
    blocks = [list(block) for block in grouper(base, 5)]
    assert len(blocks) == 3
    assert blocks[0] == list(range(5))
    assert blocks[1] == list(range(5, 10))
    assert blocks[2] == [10, 11, 12, None, None]


def test_grouper_fillvalue():
    base = range(13)
    blocks = [list(block) for block in grouper(base, 5, fillvalue=-1)]
    assert len(blocks) == 3
    assert blocks[0] == list(range(5))
    assert blocks[1] == list(range(5, 10))
    assert blocks[2] == [10, 11, 12, -1, -1]


def test_grouper_adaptive():
    base = range(13)
    blocks = [list(block) for block in grouper_adaptive(base, 5)]
    assert len(blocks) == 3
    assert blocks[0] == list(range(5))
    assert blocks[1] == list(range(5, 10))
    assert blocks[2] == list(range(10, 13))
