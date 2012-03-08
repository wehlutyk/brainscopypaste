#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Objects to interface various data structures with NLTK
'''


# Imports
import os
from codecs import open as c_open
from re import sub
from time import ctime
from warnings import warn


# Module code

class DictNltk(object):
    '''
    A class that takes an imported datasource to convert it to a dict,
    and later save that to NLTK files
    '''
    
    def __init__(self, rootfolder, dictitems, tkey):
        # Root folder where the data is to be stored
        self.rootfolder = rootfolder
        
        # The dictionary that holds the data
        self.dictitems = dictitems
        
        # The key saying where the relevant text is in the dictitems dictionary
        self.tkey = tkey
    
    def save_files(self):
        '''
        Saves the dictionary of items to their Nltk filenames, taking text_key as the key
        '''
        
        if os.path.exists(self.rootfolder):
            oldrootfolder = self.rootfolder + '.' + sub(r' +', '-', ctime())
            warn("'" + self.rootfolder + "' already exists! Moving it to '" + oldrootfolder + "'", stacklevel=2)
            os.rename(self.rootfolder, oldrootfolder)
        
        for it in self.dictitems:
            # Create the directories
            fullpath = os.path.join(self.rootfolder, it['nltk_filename'])
            folder = os.path.split(fullpath)[0]
            
            if not os.path.exists(folder):
                os.makedirs(folder)
            f = c_open(fullpath, 'wb', encoding='utf-8')
            
            if type(it[self.tkey]) == type([]):
                for d in it[self.tkey]:
                    if len(d['_text']) > 0:
                        f.write(d['_text_stripped'])
            else:
                f.write(it[self.tkey]['_text_stripped'])
            f.close()
