#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Methods for loading and saving data structures, using pickle
'''


# Imports
import pickle


# Module code
def save(s, filepath):
    ''' Save a structure '''
    with open(filepath, 'wb') as f:
        pickle.dump(s, f)


def load(filepath):
    ''' Load a structure '''
    with open(filepath, 'rb') as f:
        s = pickle.load(f)
    return s
