#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Do the MemeTracker substitution analysis with all possible parameter
combinations."""


import os

from analyze.memetracker import build_timebag_transitions


base_command = ('python -u memetracker_substitution_analysis.py '
                '--framing {fra} --lemmatizing {lem} --same_POS {pos} '
                '--n_timebags {ntb} {b1}-{b2}')

for framing in [1]:#[0, 1]:
    
    for lemmatizing in [1]:#[0, 1]:
        
        for same_POS in [1]:#[0, 1]:
            
            for n_timebags in [2, 3, 4, 5]:
                
                for (b1, b2) in build_timebag_transitions(n_timebags):
                    
                    os.system(base_command.format(fra=framing,
                                                  lem=lemmatizing,
                                                  pos=same_POS,
                                                  ntb=n_timebags,
                                                  b1=b1,
                                                  b2=b2))
