#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Structures and methods to deal with the MemeTracker dataset
See http://memetracker.org/ for details about it
'''


# Imports
import re
import os
from codecs import open as c_open


# Module code
class MT_dataset(object):
    def __init__(self, mt_filename):
        self.mt_filename = mt_filename
        self.rootfolder = os.path.split(mt_filename)[0]
    
    def print_quotes_freq(self):
        '''
        Reads the clusters file and prints out in another file what quotes are present, along with their frequencies
        '''
        
        # Open the files
        outfilename = os.path.join(self.rootfolder, 'quotes_and_frequency')
        infile = c_open(self.mt_filename, 'rb', encoding='utf-8')
        outfile = c_open(outfilename, 'wb', encoding='utf-8')
        
        # Skip the first lines
        for i in range(6):
            infile.readline()
        
        # Parse it all
        print 'Reading cluster file and writing the quotes and frequencies...',
        for line in infile:
            if line[0] == '\t' and line[1] != '\t':
                tokens = line.split('\t')
                outfile.write(u'%s\t%d\n' % (tokens[3], int(tokens[1])))
        print 'done'
        
        # Clean up and return the created file name
        infile.close()
        outfile.close()
        return outfilename

    def print_quote_ids(self):
        '''
        Reads the cluster file and prints out on each line all the quotes that belong to the same cluster
        (Was called 'leskovec_clusters_encoding.py', changed to this name to reflect what is does)
        '''
        
        # Open the files
        outfilename = os.path.join(self.rootfolder, 'quote_ids')
        infile = c_open(self.mt_filename, 'rb', encoding='utf-8')
        outfile = c_open(outfilename, 'wb', encoding='utf-8')
        
        # Skip the first few lines
        for i in range(6):
            infile.readline()
        
        # Parse it all
        print 'Reading cluster file and writing quote ids...',
        clust = []
        j = 0
        for line in infile:
            line0 = re.split(r'[\xa0\s+\t\n]+', line)
            if line0[0] != '':
                clust.append([])
            if line[0] == '\t' and line[1] != '\t':
                clust[-1].append(j)
                j += 1
        
        for cl in clust:
            for x in cl:
                outfile.write('%d ' % x)
            outfile.write('\n')
        
        print 'done'
        
        # Clean up and return the created file name
        infile.close()
        outfile.close()
        return outfilename
