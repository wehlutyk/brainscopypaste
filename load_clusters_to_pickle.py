#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Load all Clusters and save them to a pickled file
'''


# Imports
import datainterface.picklesaver as ps
import datainterface.memetracker as mt
import os


# Code
#filename = 'clust-cropped-50000.txt'
filename = 'clust-qt08080902w3mfq5.txt'
rootfolder = '/home/sebastien/Code/cogmaster-stage/data/MemeTracker/'
picklefile = os.path.join(rootfolder, 'clusters_') + filename + '.pickle'

# Check that the destination doesn't already exist
if os.path.exists(picklefile):
    raise Exception("File '" + picklefile + "' already exists!")

# Load the data
MT = mt.MT_dataset(os.path.join(rootfolder, filename))
MT.load_clusters()

# And save it
print 'Saving Clusters to pickle file...',
ps.save(MT.clusters, picklefile)
print 'done'
