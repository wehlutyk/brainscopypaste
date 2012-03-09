#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Code adapted from http://code.activestate.com/recipes/573463/ (r7)
'''
This module is for translating an XML file into a list/dict structure
It can also specially parse text tags (e.g. body of a post, like <description>
in Spinn3r XML data, and extract outward links
'''


# Imports
from __future__ import division
from xml.etree import ElementTree
from HTMLParser import HTMLParser
import nltk


# Module Code:
class XmlDictObject(dict):
    '''
    Adds object like functionality to the standard dictionary.
    '''

    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)
    
    def __getattr__(self, item):
        return self.__getitem__(item)
    
    def __setattr__(self, item, value):
        self.__setitem__(item, value)
    
    def __str__(self):
        if self.has_key('_text'):
            return self.__getitem__('_text')
        else:
            return ''

    @staticmethod
    def Wrap(x):
        '''
        Static method to wrap a dictionary recursively as an XmlDictObject
        '''

        if isinstance(x, dict):
            return XmlDictObject((k, XmlDictObject.Wrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject.Wrap(v) for v in x]
        else:
            return x

    @staticmethod
    def _UnWrap(x):
        if isinstance(x, dict):
            return dict((k, XmlDictObject._UnWrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject._UnWrap(v) for v in x]
        else:
            return x
        
    def UnWrap(self):
        '''
        Recursively converts an XmlDictObject to a standard dictionary and returns the result.
        '''

        return XmlDictObject._UnWrap(self)


class TextHtmlParser(HTMLParser):
    '''
    Can parse the body or title of a blog post (e.g. <description> or
    <title> tags in Spinn3r data), and return outward links in the format
    of a list. Each outward link is represented by a dictionary containing
    attributename,value keypairs (or a list of values for an attribute that
    has multiple instances)
    '''
     
    def __init__(self):
        HTMLParser.__init__(self)
        self.outlinks = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            # Convert the attrs argument to a dictionary with lists if an attribute has multiple instances
            attrsdict = {}
            for attr in attrs:
                if attrsdict.has_key(attr[0]):
                    # found duplicate attribute, force a list
                    if type(attrsdict[attr[0]]) is type([]):
                        # append to existing list
                        attrsdict[attr[0]].append(attr[1])
                    else:
                        # convert to list
                        attrsdict[attr[0]] = [attrsdict[attr[0]], attr[1]]
                else:
                    # only one, directly set the dictionary
                    attrsdict[attr[0]] = attr[1]
            
            self.outlinks.append(attrsdict)


def _ConvertXmlToDictRecurse(node, text_tags, dictclass):
    nodedict = dictclass()
    
    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))
    
    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, text_tags, dictclass)
        if nodedict.has_key(child.tag):
            # found duplicate tag, force a list
            if type(nodedict[child.tag]) is type([]):
                # append to existing list
                nodedict[child.tag].append(newitem)
            else:
                # convert to list
                nodedict[child.tag] = [nodedict[child.tag], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[child.tag] = newitem

    if node.text is None: 
        text = ''
    else: 
        text = node.text.strip()

    if not isinstance(text, unicode):
        text = unicode(text, 'utf-8')

    if node.tag in text_tags:
        # If we're in some kind of text node, strip the text and get outward links
        texthtmlparser = TextHtmlParser()
        text = texthtmlparser.unescape(text)
        text_stripped = nltk.clean_html(text)
        texthtmlparser.feed(text)
        text_outlinks = texthtmlparser.outlinks
        
        if not isinstance(text, unicode):
            text = unicode(text, 'utf-8')
        if not isinstance(text_stripped, unicode):
            text_stripped = unicode(text_stripped, 'utf-8')
        for link in text_outlinks:
            for attr in link:
                if not isinstance(link[attr], unicode):
                    link[attr] = unicode(link[attr], 'utf--8')

        nodedict['_text'] = text
        nodedict['_text_stripped'] = text_stripped
        nodedict['_text_outlinks'] = text_outlinks
    elif len(nodedict) > 0:
        # If we're not in a text node, if we have a dictionary add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        nodedict = text

    return nodedict


def ConvertXmlToDict(root, text_tags=[], dictclass=XmlDictObject):
    '''
    Converts an XML file or ElementTree Element to a dictionary
    '''

    # If a string is passed in, try to open it as a file
    if type(root) == type(''):
        root = ElementTree.parse(root).getroot()
    elif not isinstance(root, ElementTree.Element):
        raise TypeError, 'Expected ElementTree.Element or file path string'

    return dictclass({root.tag: _ConvertXmlToDictRecurse(root, text_tags, dictclass)})
