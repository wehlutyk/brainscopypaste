#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Tools to analyse data from the MemeTracker dataset
'''


# Imports
from __future__ import division
import numpy as np


# Module code
def simmons_5day_frame(cluster):
    '''
    Frame a cluster by cropping it in a +/-48h time frame around the 24h with highest activity
    '''
    raise NotImplemented


def find_max_24h(timeline):
    '''
    Find the 24h window (+/-some precision threshold) with the most activity
    '''
    
    prec = 30*60    # Half-hour precision
    n_windows = int(np.ceil(2*86400/prec))
    
    if not timeline.attrs_computed:
        timeline.compute_attrs()
    
    base_time = timeline.argmax_ipd_x_secs - 86400
    start_times = np.arange(n_windows) + base_time
    
    ipd_all = np.zeros(n_windows)
    for i, st in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1, (st, st+86400))[0][0]
    
    return start_times[np.argmax(ipd_all)]
