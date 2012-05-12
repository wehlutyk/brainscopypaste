#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load the Clusters data (framed and not framed) from pickle to redis."""


import gc

import datainterface.redistools as rt
import datainterface.picklesaver as ps
import settings as st


if __name__ == '__main__':
    
    # Parameters for testing, not doing the full-blown loading.
    #picklefile = st.memetracker_test_pickle
    #picklefile_framed = st.memetracker_test_framed_pickle
    #clusters_filtered_pickle = st.memetracker_test_filtered_pickle
    #clusters_ff_pickle = st.memetracker_test_ff_pickle
    
    clusters_pickle = st.memetracker_full_pickle
    clusters_framed_pickle = st.memetracker_full_framed_pickle
    clusters_filtered_pickle = st.memetracker_full_filtered_pickle
    clusters_ff_pickle = st.memetracker_full_ff_pickle
    
    # The redis connection
    
    print 'Opening connection to the redis server...',
    rserver = rt.PRedis('localhost')
    print 'OK'
    
    # Load and save the unframed clusters
    
    print 'Loading full clusters from pickle...',
    clusters = ps.load(clusters_pickle)
    print 'OK'
    
    print 'Storing full clusters to redis...',
    
    for cl_id, cl in clusters.iteritems():
        assert rserver.pset(st.redis_mt_clusters_pref, cl_id, cl)
    
    assert rserver.save()
    print 'OK'
    
    # Clean up before going to the framed clusters
    
    print 'Garbage collecting before doing the framed clusters...',
    del clusters
    gc.collect()
    print 'OK'
    
    # Load and save the framed clusters
    
    print 'Loading framed clusters from pickle...',
    clusters_framed = ps.load(clusters_framed_pickle)
    print 'OK'
    
    print 'Storing framed clusters to redis...',
    
    for cl_id, cl in clusters_framed.iteritems():
        assert rserver.pset(st.redis_mt_clusters_framed_pref, cl_id, cl)
    
    assert rserver.save()
    print 'OK'
    
    # Clean up before going to the filtered clusters
    
    print 'Garbage collecting before doing the filtered clusters...',
    del clusters_framed
    gc.collect()
    print 'OK'
    
    # Load and save the filtered clusters
    
    print 'Loading filtered clusters from pickle...',
    clusters_filtered = ps.load(clusters_filtered_pickle)
    print 'OK'
    
    print 'Storing filtered clusters to redis...',
    
    for cl_id, cl in clusters_filtered.iteritems():
        assert rserver.pset(st.redis_mt_clusters_filtered_pref, cl_id, cl)
    
    assert rserver.save()
    print 'OK'
    
    # Clean up before going to the framed-filtered clusters
    
    print 'Garbage collecting before doing the framed-filtered clusters...',
    del clusters_filtered
    gc.collect()
    print 'OK'
    
    # Load and save the framed-filtered clusters
    
    print 'Loading framed-filtered clusters from pickle...',
    clusters_ff = ps.load(clusters_ff_pickle)
    print 'OK'
    
    print 'Storing framed-filtered clusters to redis...',
    
    for cl_id, cl in clusters_ff.iteritems():
        assert rserver.pset(st.redis_mt_clusters_ff_pref, cl_id, cl)
    
    assert rserver.save()
    print 'OK'
    
    print 'All done, exiting.'
