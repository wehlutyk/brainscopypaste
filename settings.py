#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Global settings for files and folders, for the scripts to run."""


# Imports
import os


# Root folder for all the data. If we do this properly, this could be the only setting to change between computers :-)
data_root = '/home/sebastien/Code/cogmaster-stage/data'

# Folder for MemeTracker data, relative to dataroot
memetracker_root_rel = 'MemeTracker'
memetracker_root = os.path.join(data_root, memetracker_root_rel)

# File for the complete MemeTracker dataset, relative to memetracker_root
memetracker_full_rel = 'clust-qt08080902w3mfq5.txt'
memetracker_full = os.path.join(memetracker_root, memetracker_full_rel)

# File for a subset of the MemeTracker dataset for testing algorithms before a full-blown run, relative to memetracker_root
memetracker_test_rel = 'clust-cropped-50000.txt'
memetracker_test = os.path.join(memetracker_root, memetracker_test_rel)
