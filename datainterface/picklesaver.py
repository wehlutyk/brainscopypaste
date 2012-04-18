#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Save or load any data in pickle format.

Methods:
  * save: save a structure to a file
  * load: load a structure from a file

"""


import cPickle


def save(s, filepath):
    """Save a structure to a file.
    
    Arguments:
      * s: the structure to save
      * filepath: full path to the file to save to
    
    """
    
    with open(filepath, 'wb') as f:
        cPickle.dump(s, f, cPickle.HIGHEST_PROTOCOL)


def load(filepath):
    """Load a structure from a file.
    
    Arguments:
      * filepath: full path to the file to load from
    
    Returns: the loaded structure.
    
    """
    
    with open(filepath, 'rb') as f:
        s = cPickle.load(f)
    
    return s
