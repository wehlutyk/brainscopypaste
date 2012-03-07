# -*- coding: utf-8 -*-
'''
Objects that take an imported datasource to convert it to a dict,
and later save that to NLTK files
'''


# Imports
import os
from codecs import open as c_open
from re import sub
from time import ctime
from warnings import warn

# Module code
class DictNltk():
    def __init__(self, rootfolder, dictitems):
        self.rootfolder = rootfolder
        self.dictitems = dictitems
    
    def save_files(self):
        '''
        Saves the dictionary of items to their Nltk filenames
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
            
            if type(it['description']) == type([]):
                for d in it['description']:
                    if len(d['_text']) > 0:
                        f.write(d['_text_stripped'])
            else:
                f.write(it['description']['_text_stripped'])
            f.close()
