#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load all Clusters from the MemeTracker dataset and save them to a pickle file."""


# Imports
import datainterface.picklesaver as ps
import datainterface.memetracker as di_mt
import analyze.memetracker as a_mt
import settings as st


# Code
#filename = st.memetracker_test
#picklefile = st.memetracker_test_pickle
#picklefile_framed = st.memetracker_test_framed_pickle
filename = st.memetracker_full
picklefile = st.memetracker_full_pickle
picklefile_framed = st.memetracker_full_framed_pickle

# Check that the destination doesn't already exist
st.check_file(picklefile)
st.check_file(picklefile_framed)

# Load the data
MT = di_mt.MT_dataset(filename)
MT.load_clusters()

# And save it
print 'Saving Clusters to pickle file...',
ps.save(MT.clusters, picklefile)
print 'OK'

# Frame the clusters
print 'Computing framed clusters...',
framed_clusters = {}
for cl_id, cl in MT.clusters.iteritems():
    framed_clusters[cl_id] = a_mt.frame_cluster_around_peak(cl)
print 'OK'

# And save the framed clusters
print 'Saving Framed Clusters to pickle file...',
ps.save(framed_clusters, picklefile_framed)
print 'OK'
