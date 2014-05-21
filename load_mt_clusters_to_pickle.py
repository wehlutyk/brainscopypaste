#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load Clusters from the MemeTracker dataset, and save the full clusters, the
framed clusters, and the framed-filtered clusters to pickle files."""


from __future__ import division

import gc

import datainterface.picklesaver as ps
import datainterface.mt as di_mt
from util.generic import ProgressInfo
import mine.filters as m_fi
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Parameters for testing, not doing the full-blown loading.
    #filename = st.mt_test
    #picklefile = st.mt_test_pickle
    #picklefile_framed = st.mt_test_framed_pickle
    #picklefile_filtered = st.mt_test_filtered_pickle
    #picklefile_ff = st.mt_test_ff_pickle

    filename = st.mt_full
    picklefile = st.mt_full_pickle
    picklefile_framed = st.mt_full_framed_pickle
    picklefile_filtered = st.mt_full_filtered_pickle
    picklefile_ff = st.mt_full_ff_pickle

    # Check that the destination doesn't already exist.
    di_fs.check_file(picklefile)
    di_fs.check_file(picklefile_framed)
    di_fs.check_file(picklefile_filtered)
    di_fs.check_file(picklefile_ff)

    # Load the data. Set some parameters.
    MT = di_mt.MT_dataset(filename)
    MT.load_clusters()

    min_tokens = 5
    max_days = 80

    # And save it.
    print 'Saving Clusters to pickle file...',
    ps.save(MT.clusters, picklefile)
    print 'OK'

    # Frame the clusters.
    print 'Computing framed Clusters...'
    framed_clusters = {}
    progress = ProgressInfo(len(MT.clusters), 100, 'clusters')

    for cl_id, cl in MT.clusters.iteritems():

        progress.next_step()
        framed_cl = m_fi.frame_cluster_around_peak(cl)
        if framed_cl is not None:
            framed_clusters[cl_id] = framed_cl

    print 'OK'

    # Filter the clusters.
    print ('Computing filtered Clusters (min_tokens={}, '
           'max_days={})...').format(min_tokens, max_days)
    filtered_clusters = {}
    progress = ProgressInfo(len(MT.clusters), 100, 'clusters')

    for cl_id, cl in MT.clusters.iteritems():

        progress.next_step()
        filtered_cl = m_fi.filter_cluster(cl, min_tokens, max_days)
        if filtered_cl is not None:
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
    progress = ProgressInfo(len(framed_clusters), 100, 'clusters')

    for cl_id, cl in framed_clusters.iteritems():

        progress.next_step()
        ff_cl = m_fi.filter_cluster(cl, min_tokens)
        if ff_cl is not None:
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
