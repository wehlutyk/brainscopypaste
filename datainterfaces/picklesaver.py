#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Methods for loading and saving data structures, using pickle
'''


# Imports
import pickle
from codecs import open as c_open


# Module code
def save(s, filepath):
    ''' Save a structure '''
    with c_open(filepath, 'wb', encoding='utf-8') as f:
        pickle.dump(s, f)


def load(filepath):
    ''' Load a structure '''
    with c_open(filepath, 'rb', encoding='utf-8') as f:
        s = pickle.load(f)
    return s
