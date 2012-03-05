# -*- coding: utf-8 -*-
'''
Methods to convert Spinn3r XML data to an NLTK corpus reader
'''


# Imports
from dataparsing.xmlparsing.XmlDictObject import XmlDictObject, ConvertXmlToDict
from nltk.corpus.reader.plaintext import CategorizedPlaintextCorpusReader
from warnings import warn
import os
import time
import re
import hashlib
import codecs


# Module code
def ConvertSpinn3rToDict(root, dictclass=XmlDictObject):
    '''
    Converts a Spinn3r XML file or ElementTree Element to a dictionary.
    For each item, it adds a hash of the guid and a filename for use by nltk.
    It returns the first meaningful level of data: the list of <item>s.
    '''
    
    dictxml = ConvertXmlToDict(root, text_tags=['description','title'], dictclass=dictclass)
    for i, it in enumerate(dictxml.dataset.item):
        guid_sha1 = hashlib.sha1(it['guid']).hexdigest()
        it['guid_sha1'] = guid_sha1
        it['nltk_filename'] = os.path.join(it['date_found'][:10], it['publisher_type'], '{}-'.format(i) + guid_sha1 + '.txt')
    return dictxml.dataset.item


def SaveNltkFiles(rootfolder, dictitems):
    '''
    Saves a dictionary of items to their Nltk filenames
    '''
    
    if os.path.exists(rootfolder):
        otherrootfolder = rootfolder + '.' + re.sub(r' +', '-', time.ctime())
        warn("'" + rootfolder + "' already exists! Moving it to '" + otherrootfolder + "'", stacklevel=2)
        os.rename(rootfolder, otherrootfolder)
    
    for it in dictitems:
        # Create the directories
        fullpath = os.path.join(rootfolder, it['nltk_filename'])
        folder = os.path.split(fullpath)[0]
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        f = codecs.open(fullpath, 'wb', encoding='utf-8')
        
        if type(it['description']) == type([]):
            for d in it['description']:
                if len(d['_text']) > 0:
                    f.write(d['_text_stripped'])
        else:
            f.write(it['description']['_text_stripped'])
        f.close()


def CreateSpinn3rCategorizedPlaintextCorpusReader(rootfolder, filename):
    '''
    Creates a CategorzedPlaintextCorpusReader based on a stripped Spinn3r XML file
    '''
    
    dictitems = ConvertSpinn3rToDict(os.path.join(rootfolder, filename))
    rootfolder_nltk = os.path.join(rootfolder, 'nltk')
    SaveNltkFiles(rootfolder_nltk, dictitems)
    return CategorizedPlaintextCorpusReader(root=rootfolder_nltk, fileids=r'.*', cat_pattern=r'[^/]+/([^/]+)/.*')
