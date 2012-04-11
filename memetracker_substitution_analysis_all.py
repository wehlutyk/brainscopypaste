#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Do the MemeTracker substitution analysis with all possible parameter combinations."""


# Imports

from analyze.memetracker import build_timebag_transitions
import os


# Code

base_command = 'python -u memetracker_substitution_analysis.py \
--framing {fra} --lemmatizing {lem} --synonyms {syn} --ntimebags {ntb} {b1}-{b2}'

for framing in [0, 1]:
    
    for lemmatizing in [0, 1]:
        
        for synonyms_only in [0, 1]:
            
            for n_timebags in [2, 3]:
                
                for (b1, b2) in build_timebag_transitions(n_timebags):
                    
                    os.system(base_command.format(fra=framing, \
                                                  lem=lemmatizing, \
                                                  syn=synonyms_only, \
                                                  ntb=n_timebags, \
                                                  b1=b1, \
                                                  b2=b2))
