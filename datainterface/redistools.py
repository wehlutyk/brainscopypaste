#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load and save python objects to redis."""


import re
import cPickle
import copy_reg
import types
from time import sleep

import redis


#
# This little hack lets us pickle instancemethods
#

# ----- start hack -----

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

# ----- end hack -----


class PRedis(redis.Redis):

    """Add methods to :class:`~redis.Redis` to load and save python objects to
    a redis database.

    This subclass of :class:`~redis.Redis` makes storing and loading picklable
    python objects straightforward.

    .. todo:: find Redis doc to link in intersphinx

    Methods
    -------
    pset()
        Store an object serialized by pickle.
    pget()
        Load an object unserialized by pickle.
    bgsave_wait()
        Save the Redis db to disk in the background, waiting for it to finish.

    See Also
    --------
    redis.Redis

    """

    def pset(self, pref, name, obj):
        """Store an object serialized by pickle.

        The object is first serialized using :mod:`pickle`, then stored in
        Redis under the key ``pref + name``.

        Parameters
        ----------
        pref : string
            Prefix for the storage key.
        name : string
            Name of the key to store `obj` at.
        obj : picklable
            Object to store.

        Returns
        -------
        r : bool
            The result of the :meth:`~redis.Redis.set` operation.

        See Also
        --------
        .picklesaver.save

        """

        return self.set(pref + str(name),
                        cPickle.dumps(obj, protocol=cPickle.HIGHEST_PROTOCOL))

    def pget(self, pref, name):
        """Load an object unserialized by pickle.

        The serialized form is fetched from Redis under the key
        ``pref + name``, then unserialized using :mod:`pickle`.

        Parameters
        ----------
        pref : string
            Prefix for the storage key.
        name : string
            Name of the key to load `object` from.

        Returns
        -------
        obj : picklable
            The loaded object.

        See Also
        --------
        .picklesaver.load

        """

        return cPickle.loads(self.get(pref + str(name)))

    def bgsave_wait(self):
        """Save the Redis db to disk in the background, waitng for it to
        finish.

        This method will not return until the save operation is done.

        """

        try:

            self.bgsave()

        except redis.exceptions.ResponseError:

            print ('Redis is saving the DB in the background... waiting for '
                   'it to finish before triggering a new save (seconds '
                   'elapsed:'),
            isbgsaving = True
            i = 0

            while isbgsaving:

                try:

                    self.bgsave()

                except redis.exceptions.ResponseError:

                    i += 1
                    sleep(1)
                    print i,
                    continue

                else:

                    print ') OK'
                    isbgsaving = False

        print 'Saving the redis DB to disk ... (seconds elapsed:',
        lastsave = self.lastsave()
        i = 0

        while self.lastsave() == lastsave:

            i += 1
            sleep(1)
            print i,

        print ') OK'


class RedisReader(object):

    """Mimick the behaviour of a dict for data stored in Redis.

    An instance of this class can be used like any python dict, with the
    exception that it expects integer keys. It lets you transparently read
    objects from Redis using the dict syntax.

    Parameters
    ----------
    pref : string
        Prefix for all the keys at which data is read (like a namespace).

    Raises
    ------
    ValueError
        If a key under the given namespace does not represent an integer.

    Methods
    -------
    iteritems()
        Iterate through items like :meth:`dict.iteritems`.
    itervalues()
        Iterate through values like :meth:`dict.itervalues`.
    iterkeys()
        Iterate through keys like :meth:`dict.iterkeys`.
    __iter__()
        Iteration interface, like :meth:`dict.__iter__`.
    __len__()
        Length interface, like :meth:`dict.__len__`.
    __getitem__()
        Item getter, like :meth:`dict.__getitem__`.

    See Also
    --------
    dict, PRedis

    Examples
    --------
    >>> pr = PRedis()
    >>> pr.pset('mydata', 0, [1, 2, 3])  # Integer key
    True
    >>> rr = RedisReader('mydata')
    >>> rr[0]
    [1, 2, 3]

    """

    def __init__(self, pref):
        """Set the prefix for keys in the datastore."""

        self._pref = pref
        self._rserver = PRedis('localhost')
        self._keys = [int(re.sub(pref, '', s)) for s in
                      self._rserver.keys(pref + '*')]

    def iteritems(self):
        """Iterate through items like :meth:`dict.iteritems`.

        Keys are given without the prefix.

        """

        for k in self._keys:
            yield (k, self._rserver.pget(self._pref, k))

    def itervalues(self):
        """Iterate through values like :meth:`dict.itervalues`."""

        for k in self._keys:
            yield self._rserver.pget(self._pref, k)

    def iterkeys(self):
        """Iterate through keys like :meth:`dict.iterkeys`.

        Keys are given without the prefix.

        """

        for k in self._keys:
            yield k

    def __iter__(self):
        """Iteration interface, like :meth:`dict.__iter__`."""

        for k in self._keys:
            yield k

    def __len__(self):
        """Length interface, like :meth:`dict.__len__`."""

        return len(self._keys)

    def __getitem__(self, name):
        """Item getter, like :meth:`dict.__getitem__`."""

        return self._rserver.pget(self._pref, name)
