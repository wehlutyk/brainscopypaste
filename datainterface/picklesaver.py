#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Methods to save or load any data in pickle format

Methods:
  * save: save a structure to a file
  * load: load a structure from a file
"""


# Imports
import pickle


# Module code
def save(s, filepath):
    """Save a structure to a file.
    
    Arguments:
      * s: the structure to save
      * filepath: full path to the file to save to
    """
    
    with open(filepath, 'wb') as f:
        pickle.dump(s, f)


def load(filepath):
    """Load a structure from a file.
    
    Arguments:
      * filepath: full path to the file to load from
    
    Returns: the loaded structure.
    """
    
    with open(filepath, 'rb') as f:
        s = pickle.load(f)
    return s
