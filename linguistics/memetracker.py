#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Linguistic analysis tools for the MemeTracker dataset.

TODO: this module needs more commenting
TODO: this module needs cleaning up

"""


# Imports
#import sys
#import re
#import lang_detection as ld
import numpy as np
from nltk import word_tokenize 


# Module code
def levenshtein(s1, s2):
    """Compute levenshtein distance between s1 and s2."""

    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    
    if not s2:
        return len(s1)
    
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1    # j+1 instead of j since previous_row and current_row
            deletions = current_row[j] + 1          # current_row are one character longer than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row 
    
    return previous_row[-1]


def levenshtein_word(s1, s2):
    """Compute levenshtein distance between s1 and s2, taking words as the editing unit."""
    return levenshtein(word_tokenize(s1), word_tokenize(s2))


def timebag_levenshtein_closedball(timebag, center_string, d):
    """Get the stings in a TimeBag that are at levenshtein-distance d from a string."""
    distances = np.array([ levenshtein(center_string, bag_string) for bag_string in timebag.strings ])
    idx = np.where(distances <= d)
    if len(idx) > 0:
        return idx[0].tolist()
    else:
        return []


def timebag_levenshtein_word_closedball(timebag, center_string, d):
    """Get the stings in a TimeBag that are at levenshtein_word-distance d from a string."""
    distances = np.array([ levenshtein_word(center_string, bag_string) for bag_string in timebag.strings ])
    idx = np.where(distances <= d)
    if len(idx) > 0:
        return idx[0].tolist()
    else:
        return []


#infile = open('quotes_and_frequency','r')
#infile2 = open('clusters_leskovec','r')
#infile3 = open('tagged_quotes_new','r')
#infile4 = open('quotes_new','r')
#
#dist = sys.argv[1]
#
#outfilename = 'word_robustness_dist'+dist
#outfile = open(outfilename,'w')
#
#landet = ld.LangDetect()

#freq = []
#line = infile.readline()
#while line:
#    line0 = re.split(r'\t+',line)
#    freq.append(int(line0[1]))
#    line = infile.readline()
#
#quotes = []
#i = 0
#line = infile4.readline()
#while line:
#    line0 = re.split(r'\s+',line)
#    quotes.append([])
#    for x in line0:
#        if x != '':
#            quotes[i].append(x)
#    i += 1
#    line = infile4.readline()
#
#clust = []
#i = 0
#line = infile2.readline()
#while line:
#    clust.append([])
#    line0 = re.split(r'\s+',line) 
#    for x in line0:
#        if x != '':
#            clust[i].append(int(x))
#    i += 1
#    line = infile2.readline()
#
#tags = []
#line = infile3.readline()
#i = 0
#while line:
#    tags.append([])
#    line0 = re.split(r'\s+',line) 
#    for tag in line0:
#        if tag != '':
#            tags[i].append(tag)
#    i += 1
#    line = infile3.readline()
#
#print 'files are read'
#
#clust_id = [0]*len(quotes)
#for i in range(len(clust)):
#    for j in clust[i]:
#        clust_id[j] = i
#
#neighbors = [] #neighbors at distance 'dist' of each quote, it contains also the quote itsself
#for i in range(len(quotes)):
#    neighbors.append([])
#    for j in clust[clust_id[i]]:
#            lev_dist = levenshtein(quotes[i],quotes[j])
#            if lev_dist <= dist:
#                neighbors[i].append(j)
#del clust,clust_id
#
#print 'neighbors vector is created'
#
#corpus0 = {}
#new_quotes = [] #there is a list for every quote (which is empty if the quote is not in english) and each list contains a list for every word in the quotes composed of three elements: the word, the grammatical tag and the number of times the word appears in the quote with that grammatical type
#for i in range(len(quotes)):
#    new_quotes.append([])
#    if landet.detect(quotes[i]) == 'en':
#        for k in range(len(quotes[i])):
#            if quotes[i][k] not in corpus0: corpus0[quotes[i][k]] = [tags[i][k]]
#            else:
#                if tags[i][k] not in corpus0[quotes[i][k]]: corpus0[quotes[i][k]].append(tags[i][k])
#            control = 0
#            for j in range(len(new_quotes[i])):
#                if quotes[i][k] == new_quotes[i][j][0] and tags[i][k] == new_quotes[i][j][1]:
#                    new_quotes[i][j][2] += 1;
#                    control = 1
#            if control == 0:
#                new_quotes[i].append([quotes[i][k],tags[i][k],1])
#del quotes
#
#print 'new_quotes list is created'
#
#corpus = []
#for i,t in corpus0.iteritems():
#    for e in t:
#        corpus.append([i,e])
#del corpus0
#
#robustness = []
#for i in range(len(new_quotes)):
#    robustness.append([])
#    for j in range(len(new_quotes[i])):
#        num = 0; den = 0;
#        for k in neighbors[i]:
#            control = 0
#            for l in range(len(new_quotes[k])):
#                if new_quotes[k][l][0] == new_quotes[i][j][0] and new_quotes[k][l][1] == new_quotes[i][j][1]:
#                    if new_quotes[k][l][2] >= new_quotes[i][j][2]:
#                        num += freq[k]; den += freq[k]
#                    else: den += freq[k]
#                    control = 1
#            if control == 0: den += freq[k]
#        robustness[i].append(float(num)/float(den))
#
#print 'robustness vector is created'
#
#print len(corpus)
#R_num = [0]*len(corpus)
#R_den = [0]*len(corpus)
#for i in range(len(new_quotes)):
#    if i % 25000 == 0: print i
#    for j in range(len(new_quotes[i])):
#        ind = corpus.index([new_quotes[i][j][0],new_quotes[i][j][1]])
#        R_num[ind] += robustness[i][j]*freq[i]
#        R_den[ind] += freq[i]
#
#print 'calculations are over, the program is now printing on the outfile'
#
##outfile.write('word\tsize\ttype\tfreq\trobustness\n')
#for i in range(len(R_num)):
#    outfile.write('%s\t%d\t%s\t%d\t%f\n'%(corpus[i][0],len(corpus[i][0]),corpus[i][1],R_den[i],float(R_num[i])/float(R_den[i])))
