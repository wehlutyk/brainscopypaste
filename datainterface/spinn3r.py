#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load data from the custom XML Spinn3r data format into an NLTK Reader.

Classes:
  * Spinn3rCategorizedPlaintextCorpusReader: load data from the custom XML
                                             Spinn3r data format into an NLTK
                                             Reader

Methods:
  * StripXmlNamespaces: convert a Spinn3r XML into a valid XML file (used by
                        'Spinn3rCategorizedPlaintextCorpusReader')

"""


from __future__ import division

from codecs import open as c_open
import os
import hashlib
import re

from nltk.corpus.reader.plaintext import CategorizedPlaintextCorpusReader

from datainterface.xmlparsing import ConvertXmlToDict
from datainterface.nltktools import DictNltk


class Spinn3rCategorizedPlaintextCorpusReader(
        CategorizedPlaintextCorpusReader):
    
    """Load data from the custom XML Spinn3r data format into an NLTK Reader.
    
    This is used to go from a raw Spinn3r XML data file to a usable NLTK
    Reader: this class is a subclass of 'CategorizedPlaintextCorpusReader'
    which overloads '__init__' to load directly from a raw Spinnn3r XML file.
    
    Methods:
      * __init__: create a CategorizedPlaintextCorpusReader (= parent class
                  of self) from a raw Spinn3r XML file
      * ConvertSpinn3rToDict: load a stripped Spinn3r XML file into a dict;
                              this is used by '__init__', and need not be used
                              by the end user
    
    """
    
    def __init__(self, rootfolder, filename=None,
                 nltkfiles_are_present=False):
        """Create a CategorizedPlaintextCorpusReader (= parent class of self)
        from a raw Spinn3r XML file.
        
        Arguments:
          * rootfolder: the folder where 'filename' is located; an 'nltk'
                        folder will be created in this folder, where the NLTK
                        files will be saved
        
        Optional arguments -- ONE and only one of these two arguments must be
                              given:
          * filename: the raw Spinn3r XML file to load data from; it need not
                      be stripped from namespaces (i.e. it really is the raw
                      data from Spinn3r), since this is done internally by
                      '__init__'
          * nltkfiles_are_present: boolean saying if the NLTK files
                                   corresponding to the Spinn3r data have
                                   already been created, or if they need to be
                                   created. False (default): the 'filename'
                                   argument must be present, and that file
                                   will be parsed as a raw Spinn3r XML. True:
                                   that the NLTK files have already been
                                   created, and there is no need to give the
                                   'filename' argument.
        
        """
        
        # Set class variables.
        
        self.rootfolder = rootfolder
        self.nltkfolder = os.path.join(rootfolder, 'nltk')
        
        if nltkfiles_are_present == False:
            
            if filename == None:
                raise Exception(('Bad set of arguments: '
                                 "'nltkfiles_are_present == False' and "
                                 'I have no XML filename to parse'))
            
            # The NLTK files are not yet created, we should parse the XML and
            # create the files.
            
            strippedfilename = StripXmlNamespaces(os.path.join(rootfolder,
                                                               filename))
            dictitems = self.ConvertSpinn3rToDict(strippedfilename)
            
            # Save that dictionary to Nltk files.
            # 'description' is the key corresponding to textual nodes
            # (see DictNltk doc).
            
            dn = DictNltk(self.nltkfolder, dictitems, 'description')
            dn.save_files()
        
        else:
            
            # The NLTK files are already created, no need to parse the XML.
            
            if filename != None:
                
                raise Exception(('Bad set of arguments: I have an XML '
                                 'filename to parse, and '
                                 "'nltkfiles_are_present == True', "
                                 'meaning the XML is already parsed'))
        
        # Finally init the Nltk reader.
        
        CategorizedPlaintextCorpusReader.__init__(
            self, root=self.nltkfolder, fileids=r'.*',
            cat_pattern=r'[^/]+/([^/]+)/.*')

    def ConvertSpinn3rToDict(self, strippedfilename):
        """Load a stripped Spinn3r XML file (i.e. valid XML) into a dict.
        
        This starts by loading the XML file to a dict (ConvertXmlToDict), and
        then adds to each item a hash of the guid and an 'nltk_filename'
        (created from that guid hash) for later use when saving that data
        to NLTK files.
        
        Arguments:
          * strippedfilename: the stripped Spinn3r XML file to load data from
        
        Returns: the final list of items, each represented by a dict (i.e. a
                 list of dicts is returned).
        
        """
        
        # Get the dict corresponding to the Spinn3r XML file.
        
        dictxml = ConvertXmlToDict(os.path.join(self.rootfolder,
                                                strippedfilename),
                                   text_tags=['description','title'])
        
        # For each item, add a guid and an Nltk filename.
        
        for i, it in enumerate(dictxml.dataset.item):
            
            guid_sha1 = hashlib.sha1(it['guid']).hexdigest()
            it['guid_sha1'] = guid_sha1
            it['nltk_filename'] = os.path.join(
                                    it['date_found'][:10],
                                    it['publisher_type'],
                                    '{}-'.format(i) + guid_sha1 + '.txt')
        
        return dictxml.dataset.item


def StripXmlNamespaces(filename, namespaces=['dc', 'weblog', 'atom', 'post',
                                             'feed', 'source']):
    """Convert a Spinn3r XML into a valid XML file.
    
    Raw Spinn3r XML files contain namespaces which are not defined in the
    file, and there is no root node containing the whole data (i.e. it's
    directly a succession of <item>...</item> tags). This makes it an invalid
    XML file which needs a few changes before parsing. This method strips all
    namespaces from the file (this results in no loss of information, the
    namespaces are useless), and adds an initial <dataset> tag at the top of
    the file and a final </dataset> tag at the end. The result is a valid,
    parsable XML file.
    
    Arguments:
      * filename: full path to the raw Spinn3r XML file
    
    Optional arguments:
      * namespaces: a list of namespaces to strip. Defaults to ['dc',
                    'weblog', 'atom', 'post', 'feed', 'source'], which are
                    the namespaces I found in the file I work on.
    
    Returns: full path to the resulting stripped XML file.
    
    """
    
    stripped_filename = re.sub(r'\.xml$', '.stripped.xml', filename)
    
    # Check the input file has a .xml extension, and do not override an
    # existing target file.
    
    if re.search(r'\.xml$', filename) == None:
        
        raise Exception(
                "'" + filename +
                "' does not end with .xml! Are you sure this is an XML file?")
        
    if os.path.exists(stripped_filename):
        
        raise Exception("'" + stripped_filename +
                        "' already exists! Will not overwrite it. Aborting.")
    
    # Do the stripping and add the start and end tags.
    
    with c_open(filename, 'rb', encoding='utf-8') as f1, \
         c_open(stripped_filename, 'wb', encoding='utf-8') as f2:
    
        ns = r'(' + r':|'.join(namespaces) + r':)'
        
        f2.write('<dataset>\n')
        
        for line in f1:
            f2.write(re.sub(ns, '', line))
        
        f2.write('</dataset>\n')
    
    return stripped_filename
