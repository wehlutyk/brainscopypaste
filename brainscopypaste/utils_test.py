"""Tests for :mod:`.utils`.

"""


import pickle
from tempfile import mkstemp
import os

import pytest

from brainscopypaste.utils import (grouper, grouper_adaptive, langdetect,
                                   is_same_ending_us_uk_spelling, is_int,
                                   levenshtein, hamming, sublists, subhamming,
                                   stopwords, memoized, cache, unpickle)


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


def test_is_same_ending_us_uk_spelling():
    assert is_same_ending_us_uk_spelling('centre', 'center')
    assert not is_same_ending_us_uk_spelling('flower', 'flower')
    assert not is_same_ending_us_uk_spelling('flower', 'bowl')
    assert not is_same_ending_us_uk_spelling('ter', 'atre')
    assert not is_same_ending_us_uk_spelling('er', 're')
    assert not is_same_ending_us_uk_spelling('centre', 'cinter')


def test_is_int():
    assert is_int('20')
    assert not is_int('20.0')
    assert not is_int('20.1')
    assert not is_int('2a')
    assert not is_int('21st')
    assert not is_int(None)
    assert not is_int(1)
    assert not is_int(1.0)
    assert not is_int(1.2)


def test_levenshtein():
    assert levenshtein('hello', 'whatever') == levenshtein('whatever', 'hello')
    assert levenshtein('hello', 'hello there') == 6
    assert levenshtein('hello', 'hallo') == 1
    assert levenshtein('hello', 'hellto') == 1
    assert levenshtein('hello', 'hell to') == 2
    assert levenshtein('hello', 'hel to') == 2
    assert levenshtein('hello', 'hl to') == 3
    assert levenshtein('hello', 'hello') == 0
    assert levenshtein('hello', '') == 5


def test_hamming():
    assert hamming('hello', 'hallo') == 1
    assert hamming('hello', 'halti') == 3
    assert hamming('hello', 'halti') == hamming('halti', 'hello')
    assert hamming('hello', 'hello') == 0
    with pytest.raises(ValueError):
        hamming('hello', 'hell')


def test_sublists():
    l = tuple(range(5))
    assert sublists(l, 0) == ()
    assert sublists(l, 1) == ((0,), (1,), (2,), (3,), (4,))
    assert sublists(l, 2) == ((0, 1), (1, 2), (2, 3), (3, 4))
    assert sublists(l, 3) == ((0, 1, 2), (1, 2, 3), (2, 3, 4))
    assert sublists(l, 4) == ((0, 1, 2, 3), (1, 2, 3, 4))
    assert sublists(l, 5) == ((0, 1, 2, 3, 4),)
    with pytest.raises(ValueError):
        sublists(l, 6)
    with pytest.raises(ValueError):
        sublists((), 2)
    with pytest.raises(TypeError) as excinfo:
        sublists([], 2)
    assert 'unhashable type' in str(excinfo.value)
    with pytest.raises(TypeError) as excinfo:
        sublists([1, 2, 3], 2)
    assert 'unhashable type' in str(excinfo.value)


def test_subhamming():
    assert subhamming('hello there sir', 'hallo') == (1, 0)
    assert subhamming('hello there sir', 'halti') == (3, 0)
    assert subhamming('hello there sir', 'e') == (0, 1)
    assert subhamming('hello there sir', '') == (15, 0)
    assert subhamming('hello there sir', 'there') == (0, 6)
    assert subhamming('hello there sir', 'sir') == (0, 12)
    with pytest.raises(ValueError):
        subhamming('hello', 'hello there dear sir')


def test_stopwords():
    assert 'a' in stopwords
    assert stopwords._loaded
    assert 'yet' in stopwords
    assert 'do' in stopwords
    assert 'Do' not in stopwords
    assert 'do ' not in stopwords


def test_memoized():
    counter = 0

    def func():
        """My super func."""
        nonlocal counter
        counter += 1
        return counter

    # Doc is propagated through memoization.
    assert func.__doc__ == 'My super func.'

    # Caching works.
    mfunc = memoized(func)
    assert mfunc() == 1
    assert mfunc() == 1
    # Dropping the cache works.
    mfunc.drop_cache()
    assert mfunc() == 2
    assert mfunc() == 2


def test_memoized_class():
    counter = 0

    class Klass:
        @memoized
        def func(self):
            """My super instance func."""
            nonlocal counter
            counter += 1
            return counter

    klass1 = Klass()
    klass2 = Klass()

    # Doc is propagated through memoization.
    assert klass1.func.__doc__ == 'My super instance func.'
    assert klass2.func.__doc__ == 'My super instance func.'
    assert Klass.func.__doc__ == 'My super instance func.'

    # Caching works on instances.
    assert klass1.func() == 1
    assert klass1.func() == 1
    # Another instance counts as different argument.
    assert klass2.func() == 2
    assert klass2.func() == 2

    # Dropping cache on the class or any of the instances has the same effect.
    klass1.func.drop_cache()
    assert klass1.func() == 3
    assert klass1.func() == 3
    assert klass2.func() == 4
    assert klass2.func() == 4
    klass2.func.drop_cache()
    assert klass1.func() == 5
    assert klass1.func() == 5
    assert klass2.func() == 6
    assert klass2.func() == 6
    Klass.func.drop_cache()
    assert klass1.func() == 7
    assert klass1.func() == 7
    assert klass2.func() == 8
    assert klass2.func() == 8


def test_memoized_class_classmethod():
    counter = 0

    class Klass:
        @classmethod
        @memoized
        def clsfunc(self):
            """My super class func."""
            nonlocal counter
            counter += 1
            return counter

    klass1 = Klass()
    klass2 = Klass()

    # Doc is propagated through memoization.
    assert klass1.clsfunc.__doc__ == 'My super class func.'
    assert klass2.clsfunc.__doc__ == 'My super class func.'
    assert Klass.clsfunc.__doc__ == 'My super class func.'

    # Caching works on the class and instances, and having a different instance
    # counts as the same argument.
    assert Klass.clsfunc() == 1
    assert klass1.clsfunc() == 1
    assert klass2.clsfunc() == 1

    # Dropping cache on the class or any of the instances has the same effect.
    Klass.clsfunc.drop_cache()
    assert Klass.clsfunc() == 2
    assert klass1.clsfunc() == 2
    assert klass2.clsfunc() == 2
    klass1.clsfunc.drop_cache()
    assert Klass.clsfunc() == 3
    assert klass1.clsfunc() == 3
    assert klass2.clsfunc() == 3
    klass2.clsfunc.drop_cache()
    assert Klass.clsfunc() == 4
    assert klass1.clsfunc() == 4
    assert klass2.clsfunc() == 4


def test_cache():

    class Klass:
        def __init__(self):
            self.counter = 0

        @cache
        def prop(self):
            self.counter += 1
            return self.counter

    klass = Klass()
    assert klass.counter == 0
    assert klass.prop == 1
    assert klass.prop == 1


def test_unpickle():
    fd, path = mkstemp()

    # Pickle an object to this temporary file.
    obj = {'a': 1}
    with os.fdopen(fd, 'wb') as file:
        pickle.dump(obj, file)

    # Check it's unpickled well.
    unpickled_obj = unpickle(path)
    assert obj == unpickled_obj
    assert obj is not unpickled_obj
    # The unpickling is cached.
    assert unpickled_obj is unpickle(path)

    # Clean up.
    os.remove(path)
