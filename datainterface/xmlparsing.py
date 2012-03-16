#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Code adapted from http://code.activestate.com/recipes/573463/ (r7)

"""Parse XML into a dict, extract links from HTML, or strip HTML from tags.

Classes:
  * TextHtmlParser: extract links (<a>...</a> tags) from HTML strings (subclass of HTMLParser)

Methods:
  * _ConvertXmlToDictRecurse: recursively convert an ElementTree Element to a dict (not meant to be used directly)
  * ConvertXmlToDict: convert an XML file or an ElementTree Element to a dict
                      (this is a wrapper for _ConvertXmlToDictRecurse and is meant to be used by the end user)

"""


# Imports
from __future__ import division
from xml.etree import ElementTree
from HTMLParser import HTMLParser
import nltk


# Module code
class TextHtmlParser(HTMLParser):
    
    """Extract links (<a>...</a> tags) from HTML strings (subclass of HTMLParser)s.
    
    This subclass only defines the starttag handler to catch opening <a> tags, and stores whatever attributes
    if finds in a dictionary for each link. The rest of the parsing is implemented by the HTMLParser, and one
    can use that class' interface to parse a string (through the 'feed' method).
    
    Methods:
      * __init__: initialize the parent class, and the future result
      * handle_starttag: handle an opening tag encountered in the HTML string, and store if it's an <a>
    
    Effects: after parsing (use the 'feed' method from HTMLParser for that), 'self.outlinks' contains a list of
             dicts, each one representing a link encountered in the HTML string. The dict contains one key per attribute
             found in the <a ...> declaration; if one attribute is specified multiple times in the same <a ...>, the
             corresponding value in the dict is a list containing those attribute values.
    
    """
    
    def __init__(self):
        """Initialize the parent class, and the future result."""
        HTMLParser.__init__(self)
        self.outlinks = []
    
    def handle_starttag(self, tag, attrs):
        """Handle an opening tag encountered in the HTML string, and store if it's an <a>."""
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


def _ConvertXmlToDictRecurse(node, text_tags):
    """Recursively convert an ElementTree Element to a dict.
    
    This method is wrapped by ConvertXmlToDict, and is not meant to be used directly.
    
    Arguments:
      * node: the ElementTree Element to work on
      * text_tags: a list of strings representing which tags contain textual data in the XML; those nodes
                   are treated as HTML: in addition to storing the text they contain, content of those nodes
                   is also stripped from HTML tags (and stored), and scanned for link declarations (which
                   are stored too)
    
    Returns: if the ElementTree Element had no subnodes, this returns a string containing whatever text the Element
             contained. If the Element had subnodes, a dict is returned: each key of the dict is a tag name, and the
             corresponding value is the result of _ConvertXmlToDictRecurse on that node; if that tag was declared
             multiple times, the value corresponding to the tag is a list of results from _ConvertXmlToDictRecurse (one
             for each declaration); any text found out of subnodes if stored under the '_text' key of the resulting dict.
             If, in addition, the Element name (tag) is in 'text_tags' (i.e. it contains textual data), then two other
             keys are added in the dict: '_text_stripped', which is the text stripped from HTML entities, and
             '_text_outlinks', which is a list of dicts, each one representing a link (<a>...</a> tag, but in HTML entity
             format) found in the text (the (key, value) pairs of those dicts are the attributes found in the <a ...>
             declarations; if an attribute was declared multiple times in an <a ...>, the value under that key is a list
             of all the declared values).
    
    """
    
    # The future result
    nodedict = {}
    
    if len(node.items()) > 0:
        # if we have attributes, set them as keys
        nodedict.update(dict(node.items()))
    
    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, text_tags)
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
    
    # Check we have unicode text; if not, convert to it
    if not isinstance(text, unicode):
        text = unicode(text, 'utf-8')

    if node.tag in text_tags:
        # If we're in some kind of text node, strip the text from HTML tags and get outward links
        texthtmlparser = TextHtmlParser()
        # This next line is to convert the HTML entities to unicode characters (e.g. '&lt;' to '<' and '&gt;' to '>')
        text = texthtmlparser.unescape(text)
        # Get the stripped text
        text_stripped = nltk.clean_html(text)
        # And the links
        texthtmlparser.feed(text)
        text_outlinks = texthtmlparser.outlinks
        
        # Check that we have unicode
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
        # If we're not in a text node, if we have a dictionary add the text as a dictionary key (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes (and we're not in a textual node), just set the text
        nodedict = text

    return nodedict


def ConvertXmlToDict(root, text_tags):
    """Convert an XML file or an ElementTree Element to a dict.
    
    This is a wrapper for _ConvertXmlToDictRecurse and is meant to be used by the end user.
    
    Arguments:
      * root: either the full path to the file to parse, or an ElementTree Element to be parsed
      * text_tags: a list of strings representing which tags contain textual data in the XML; those nodes
                   are treated as HTML: in addition to storing the text they contain, content of those nodes
                   is also stripped from HTML tags (and stored), and scanned for link declarations (which
                   are stored too)
    
    Returns: a dict representing the parsed XML; see the doc for _ConvertXmlToDictRecurse for details on the exact format.
    
    """

    # If a string is passed in, try to open it as a file
    if type(root) == type(''):
        root = ElementTree.parse(root).getroot()
    elif not isinstance(root, ElementTree.Element):
        raise TypeError, 'Expected ElementTree.Element or file path string'

    return dict({root.tag: _ConvertXmlToDictRecurse(root, text_tags)})
