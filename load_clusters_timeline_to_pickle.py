#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Load all cluster timelines and save them to a pickled file
'''


# Imports
import datainterfaces.picklesaver as ps
import datainterfaces.memetracker as mt
import os


# Code
#filename = 'clust-cropped-50000.txt'
filename = 'clust-qt08080902w3mfq5.txt'
rootfolder = '/home/sebastien/Code/cogmaster-stage/data/MemeTracker/'
savefile = os.path.join(rootfolder, 'clusters_timeline_') + filename + '.pickle'

# Check that the destination doesn't already exist
if os.path.exists(savefile):
    raise Exception("File '" + savefile + "' already exists!")

# Load the data
MT = mt.MT_dataset(os.path.join(rootfolder, filename))
MT.load_clusters_timeline()

# And save it
print 'Saving clusters_timeline to file...',
ps.save(MT.clusters_timeline, savefile)
print 'done'
