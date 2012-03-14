#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Compute a few statistics about the MemeTracker dataset
'''


# Imports
from pylab import *
from nltk import word_tokenize
import datainterface.picklesaver as ps
import analyze.memetracker as a_mt
import os


# Code
#filename = 'clust-cropped-50000.txt'
filename = 'clust-qt08080902w3mfq5.txt'
rootfolder = '/home/sebastien/Code/cogmaster-stage/data/MemeTracker/'
picklefile = os.path.join(rootfolder, 'clusters_') + filename + '.pickle'

# Load the data
print 'Loading data...',
clusters = ps.load(picklefile)
print 'done'

# FIRST: Distribution of number of quotes/clusters
# Compute the (length -> cluster ids) dictionary
print 'Computing distribution of number of quotes/cluster...',
inv_cl_lengths = a_mt.build_n_quotes_to_clusterids(clusters)

# Put that into plottable format
cl_lengths = []
cl_lengths_n = []
for l in sorted(inv_cl_lengths.keys()):
    cl_lengths.append(l)
    cl_lengths_n.append(len(inv_cl_lengths[l]))
print 'done'

# Plot it all
figure()
plot(cl_lengths, cl_lengths_n, label='Distribution du nombre de citations/cluster')
xlabel('Nombre de citations')
ylabel('Nombre de clusters')
legend()


# SECOND: Distribution of number of words/quote
# Compute the (number of words -> number of quotes) dictionary
print 'Computing distribution of number of words/quote...',
inv_qt_lengths = a_mt.build_quotelengths_to_quoteids(clusters)

# Put that into plottable format
qt_lengths = []
qt_lengths_n = []
for l in sorted(inv_qt_lengths.keys()):
    qt_lengths.append(l)
    qt_lengths_n.append(inv_qt_lengths[l])
print 'done'

# Plot it all
figure()
plot(qt_lengths, qt_lengths_n, label='Distribution du nombre de mots/quote')
xlabel('Nombre de mots')
ylabel('Nombre de quotes')
legend()
