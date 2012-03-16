#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for interfacing NLTK objects and dataset objects.

Classes:
  * DictNltk: tool to save an imported datasource (in a list of dicts) to NLTK files,
              for later importing by an NLTK reader
"""


# Imports
from __future__ import division
import os
from codecs import open as c_open
from re import sub
from time import ctime
from warnings import warn


# Module code
class DictNltk(object):
    
    """Tool to save an imported datasource (in a list of dicts) to NLTK files, for later importing by an NLTK reader.
    
    Methods:
      * __init__: initialize the class with file path info, the data, and what keys represent text in the list of dicts
      * save_files: save the immported data (in a list of dicts) to NLTK files
    """
    
    def __init__(self, nltkfolder, dictitems, tkey):
        """Initialize the class with file path info, the data, and what keys represent text in the dict.
        
        Arguments:
          * nltkfolder: the folder where the NLTK files will later be created
          * dictitmes: a list of dicts representing the imported data items. The dict items must each have an
                       'nltk_filename' key, which is used as the filename into which any textual data found in
                       that particular dict is stored. 
          * tkey: a string which is a key in each of the dicts in dictitems, indicating where, in the dicts, the textual
                  data to be saved to the NLTK files is. The item under the 'tkey' key in the dict must be a dict itself, 
                  with a '_text' key (containing a string) and, if that string is not empty, an additional '_text_stripped'
                  key containing the text from the '_text' key stripped from any unwanted stuff (e.g. HTML tags). The
                  '_text_stripped' string is what is saved to the NLTK file of that dict.
        """
        
        # Root folder where the data is to be stored
        self.nltkfolder = nltkfolder
        # The dictionary that holds the data
        self.dictitems = dictitems
        # The key saying where the relevant text is in the dictitems dictionary
        self.tkey = tkey
    
    def save_files(self):
        """Save the immported data (in a dict) to NLTK files.
        
        Effects:
          * looks at the self.tkey key in each dict of dictitem (this will fail if one dict does not have the
            self.tkey key). The item under that key must be itself a dict. It then looks at the '_text' key in
            that sub-dict: if it's not empty, it takes the '_text_stripped' key in that same dict and saves that
            to the file indicated by the 'nltk_filename' key of the 1st-level dict.
          * it will not overwrite an existing nltkfolder: if the nltkfolder already exists, it is moved to a backup,
            (printed to stdout) and the rest of the processing goes on
        """
        
        if os.path.exists(self.nltkfolder):
            oldnltkfolder = self.nltkfolder + '.' + sub(r' +', '-', ctime())
            warn("'" + self.nltkfolder + "' already exists! Moving it to '" + oldnltkfolder + "'", stacklevel=2)
            os.rename(self.nltkfolder, oldnltkfolder)
        
        for it in self.dictitems:
            # Create the directories
            fullpath = os.path.join(self.nltkfolder, it['nltk_filename'])
            folder = os.path.split(fullpath)[0]
            
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            with c_open(fullpath, 'wb', encoding='utf-8') as f:
                if type(it[self.tkey]) == type([]):
                    for d in it[self.tkey]:
                        if len(d['_text']) > 0:
                            f.write(d['_text_stripped'])
                else:
                    f.write(it[self.tkey]['_text_stripped'])
