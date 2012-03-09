#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Objects to interface Spinn3r data with other data structures
'''


# Imports
from __future__ import division
from datainterfaces.xmlparsing import ConvertXmlToDict
from datainterfaces.nltktools import DictNltk
from nltk.corpus.reader.plaintext import CategorizedPlaintextCorpusReader
from codecs import open as c_open
import os
import hashlib
import re


# Module code
class Spinn3rCategorizedPlaintextCorpusReader(CategorizedPlaintextCorpusReader):
    def __init__(self, rootfolder, filename=None, nltkfiles_are_present=False):
        '''
        Creates a CategorzedPlaintextCorpusReader based on a stripped Spinn3r XML file.
        '''
        
        # Set class variables
        self.rootfolder = rootfolder
        self.nltkfolder = os.path.join(rootfolder, 'nltk')
        
        if nltkfiles_are_present == False:
            if filename == None:
                raise Exception("Bad set of arguments: 'nltkfiles_are_present == False' and \
                                 I have no XML filename to parse")
            # The NLTK files are not yet created, we should parse the XML and create the files
            # Get the dictionary corresponding to the Spinn3r XML file
            strippedfilename = StripXmlNamespaces(os.path.join(rootfolder, filename))
            dictitems = self.ConvertSpinn3rToDict(strippedfilename)
            
            # Save that dictionary to Nltk files
            dn = DictNltk(self.nltkfolder, dictitems, 'description')
            dn.save_files()
        else:
            # The NLTK files are already created, no need to parse the XML
            if filename != None:
                raise Exception("Bad set of arguments: I have an XML filename to parse, and \
                                 'nltkfiles_are_present == True', meaning the XML is already parsed")
        
        # Finally init the Nltk reader
        CategorizedPlaintextCorpusReader.__init__(self, root=self.nltkfolder, fileids=r'.*', cat_pattern=r'[^/]+/([^/]+)/.*')

    def ConvertSpinn3rToDict(self, strippedfilename):
        '''
        Converts a Spinn3r XML file or ElementTree Element to a dictionary.
        For each item, it adds a hash of the guid and a filename for use by nltk.
        It returns the first meaningful level of data: the list of <item>s.
        '''
        
        # Get the dict corresponding to the Spinn3r XML file
        dictxml = ConvertXmlToDict(os.path.join(self.rootfolder, strippedfilename), text_tags=['description','title'])
        
        # For each item, add a guid and an Nltk filename
        for i, it in enumerate(dictxml.dataset.item):
            guid_sha1 = hashlib.sha1(it['guid']).hexdigest()
            it['guid_sha1'] = guid_sha1
            it['nltk_filename'] = os.path.join(it['date_found'][:10], it['publisher_type'], '{}-'.format(i) + guid_sha1 + '.txt')
        return dictxml.dataset.item


def StripXmlNamespaces(filename, namespaces=['dc', 'weblog', 'atom', 'post', 'feed', 'source']):
    '''
    Strip XML Namespaces from a Spinn3r XML file, and wrap the whole file in a <dataset> tag
    '''
    
    stripped_filename = re.sub(r'\.xml$', '.stripped.xml', filename)
    
    if re.search(r'\.xml$', filename) == None:
        raise Exception("'" + filename + "' does not end with .xml! Are you sure this is an XML file?")
    if os.path.exists(stripped_filename):
        raise Exception("'" + stripped_filename + "' already exists! Will not overwrite it. Aborting.")
    
    ns = r'(' + r':|'.join(namespaces) + r':)'
    
    f1 = c_open(filename, 'rb', encoding='utf-8')
    f2 = c_open(stripped_filename, 'wb', encoding='utf-8')
    
    f2.write('<dataset>\n')
    for line in f1:
        f2.write(re.sub(ns, '', line))
    f2.write('</dataset>\n')
    
    f1.close()
    f2.close()
    
    return stripped_filename
