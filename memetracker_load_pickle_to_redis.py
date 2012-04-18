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
    
    clusters_pickle = st.memetracker_full_pickle
    clusters_framed_pickle = st.memetracker_full_framed_pickle
    
    # The redis connection
    
    print 'Opening connection to the redis server...',
    rserver = rt.PRedis('localhost')
    print 'OK'
    
    # Load and save the unframed clusters
    
    print 'Loading unframed clusters from pickle...',
    clusters = ps.load(clusters_pickle)
    print 'OK'
    
    print 'Storing unframed clusters to redis...',
    
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
    
    print 'All done, exiting.'
