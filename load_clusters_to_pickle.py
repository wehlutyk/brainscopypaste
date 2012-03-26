#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load all Clusters from the MemeTracker dataset and save them to a pickle file."""


# Imports
import datainterface.picklesaver as ps
import datainterface.memetracker as mt
import settings as st


# Code
#filename = st.memetracker_test
#picklefile = st.memetracker_test_pickle
filename = st.memetracker_full
picklefile = st.memetracker_full_pickle

# Check that the destination doesn't already exist
st.check_file(picklefile)

# Load the data
MT = mt.MT_dataset(filename)
MT.load_clusters()

# And save it
print 'Saving Clusters to pickle file...',
ps.save(MT.clusters, picklefile)
print 'done'
