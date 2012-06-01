#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load and save python objects to redis.

Classes:
  * PRedis: add two methods to redis.Redis load and save python objects to a
            redis instance

"""


import re
import cPickle
import copy_reg
import types

import redis


# Let us pickle instancemethods

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


class PRedis(redis.Redis):
    
    """Add two methods to redis.Redis to load and save python objects to
    a redis instance.
    
    This is a subclass of redis.Redis.
    
    Methods:
      * pset: store an object under key 'pref + name', serialized by pickle
      * pget: load an object at key 'pref + name', unserialized by pickle
    
    """
    
    def pset(self, pref, name, obj):
        """Store an object under key 'pref + name', serialized by pickle."""
        return self.set(pref + str(name),
                        cPickle.dumps(obj, protocol=cPickle.HIGHEST_PROTOCOL))
    
    def pget(self, pref, name):
        """Load an object at key 'pref + name', unserialized by pickle."""
        return cPickle.loads(self.get(pref + str(name)))


class RedisReader(object):
    def __init__(self, pref):
        self._pref = pref
        self._rserver = PRedis('localhost')
        self._keys = [int(re.sub(pref, '', s)) for s in
                      self._rserver.keys(pref + '*')]
    
    def iteritems(self):
        for k in self._keys:
            yield (k, self._rserver.pget(self._pref, k))
    
    def itervalues(self):
        for k in self._keys:
            yield self._rserver.pget(self._pref, k)
    
    def iterkeys(self):
        for k in self._keys:
            yield k
    
    def __iter__(self):
        for k in self._keys:
            yield k
    
    def __len__(self):
        return len(self._keys)
    
    def __getitem__(self, name):
        return self._rserver.pget(self._pref, name)
