#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load all Clusters from the MemeTracker dataset and save them to a pickle file."""


# Imports
import os
import datainterface.picklesaver as ps
import datainterface.memetracker as mt
import settings as st


# Code
#filename = st.memetracker_test_rel
filename = st.memetracker_full_rel
picklefile = os.path.join(st.memetracker_root, 'clusters_') + filename + '.pickle'

# Check that the destination doesn't already exist
if os.path.exists(picklefile):
    raise Exception("File '" + picklefile + "' already exists!")

# Load the data
MT = mt.MT_dataset(os.path.join(st.memetracker_root, filename))
MT.load_clusters()

# And save it
print 'Saving Clusters to pickle file...',
ps.save(MT.clusters, picklefile)
print 'done'
