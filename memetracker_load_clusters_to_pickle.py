#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load Clusters from the MemeTracker dataset, and save the full clusters, the
framed clusters, and the framed-filtered clusters to pickle files."""


import gc

import datainterface.picklesaver as ps
import datainterface.memetracker as di_mt
import analyze.memetracker as a_mt
import settings as st


if __name__ == '__main__':
    
    # Parameters for testing, not doing the full-blown loading.
    #filename = st.memetracker_test
    #picklefile = st.memetracker_test_pickle
    #picklefile_framed = st.memetracker_test_framed_pickle
    #picklefile_filtered = st.memetracker_test_filtered_pickle
    #picklefile_ff = st.memetracker_test_ff_pickle
    
    filename = st.memetracker_full
    picklefile = st.memetracker_full_pickle
    picklefile_framed = st.memetracker_full_framed_pickle
    picklefile_filtered = st.memetracker_full_filtered_pickle
    picklefile_ff = st.memetracker_full_ff_pickle
    
    
    # Check that the destination doesn't already exist.
    
    st.check_file(picklefile)
    st.check_file(picklefile_framed)
    st.check_file(picklefile_filtered)
    st.check_file(picklefile_ff)
    
    # Load the data. Set some parameters.
    
    MT = di_mt.MT_dataset(filename)
    MT.load_clusters()
    
    min_tokens = 5
    
    
    # And save it.
    
    print 'Saving Clusters to pickle file...',
    ps.save(MT.clusters, picklefile)
    print 'OK'
    
    
    # Frame the clusters.
    
    print 'Computing framed Clusters...'
    framed_clusters = {}
    progress = a_mt.ProgressInfo(len(MT.clusters), 100, 'clusters')
    
    for cl_id, cl in MT.clusters.iteritems():
        
        progress.next_step()
        framed_cl = a_mt.frame_cluster_around_peak(cl)
        if framed_cl != None:
            framed_clusters[cl_id] = framed_cl
    
    print 'OK'
    
    
    # Filter the clusters.
    
    print 'Computing filtered Clusters (min_tokens={})...'.format(min_tokens)
    filtered_clusters = {}
    progress = a_mt.ProgressInfo(len(MT.clusters), 100, 'clusters')
    
    for cl_id, cl in MT.clusters.iteritems():
        
        progress.next_step()
        filtered_cl = a_mt.filter_cluster(cl, min_tokens)
        if filtered_cl != None:
            filtered_clusters[cl_id] = filtered_cl
    
    print 'OK'
    
    
    # Clean up before saving, this stuff is hard on memory.
    
    print ('Cleaning up before saving framed and filtered Clusters to pickle '
           'files...'),
    del MT
    gc.collect()
    print 'OK'
        
    # And save the framed an filtered clusters.
    
    print ('Saving framed Clusters to pickle file (this might take quite '
           'some time, e.g. up to 30 minutes)...'),
    ps.save(framed_clusters, picklefile_framed)
    print 'OK'
    
    print ('Saving filtered Clusters to pickle file (this might take quite '
           'some time, e.g. up to 30 minutes)...'),
    ps.save(filtered_clusters, picklefile_filtered)
    print 'OK'
    
    
    print ('Cleaning up before doing the framed-filtered clusters...'),
    del filtered_clusters
    gc.collect()
    print 'OK'
    
    
    # Frame-Filter the clusters.
    
    print ('Computing framed-filtered Clusters '
           '(min_tokens={})...').format(min_tokens)
    ff_clusters = {}
    progress = a_mt.ProgressInfo(len(MT.clusters), 100, 'clusters')
    
    for cl_id, cl in framed_clusters.iteritems():
        
        progress.next_step()
        ff_cl = a_mt.filter_cluster(cl, min_tokens)
        if ff_cl != None:
            ff_clusters[cl_id] = ff_cl
    
    print 'OK'
    
    # Clean up before saving, this stuff is hard on memory.
    
    print ('Cleaning up before saving framed-filtered '
           'Clusters to pickle file...'),
    del framed_clusters
    gc.collect()
    print 'OK'
    
    # And save the filtered clusters.
    
    print 'Saving framed-filtered Clusters to pickle file...',
    ps.save(ff_clusters, picklefile_ff)
    print 'OK'
