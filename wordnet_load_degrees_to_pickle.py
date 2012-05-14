#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the degrees for the lemmas in Wordnet, and save the scores dict to
a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


if __name__ == '__main__':
    
    for p in st.memetracker_subst_POSs:
        
        # Get the filename and check the destination doesn't exist.
        
        picklefile = st.wordnet_degrees_pickle.format(p)
        
        try:
            st.check_file(picklefile)
        except Exception:
            
            print picklefile + 'already exists, not overwriting it.'
            continue
        
        # Compute the degrees.
        
        print
        print ('*** Computing degrees for the lemmas in Wordnet '
               "(POS = '{}') ***").format(p)
        degrees = wnt.build_wn_degrees(p)
        
        # And save them.
        
        print "*** Saving the degrees to '" + picklefile + "'...",
        ps.save(degrees, picklefile)
        print 'OK'
