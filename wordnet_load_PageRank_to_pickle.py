#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compute the PageRank scores for the lemmas in Wordnet, and save the scores
dict to a pickle file."""


import datainterface.picklesaver as ps
import linguistics.wordnettools as wnt
import settings as st


if __name__ == '__main__':
    
    for p in st.memetracker_subst_POSs:
        
        # Get the filename and check the destination doesn't exist.
        
        picklefile = st.wordnet_PR_scores_pickle.format(p)
        
        try:
            st.check_file(picklefile)
        except Exception:
            
            print picklefile + 'already exists, not overwriting it.'
            continue
        
        # Compute the PR scores.
        
        print
        print ('*** Computing PR scores for the lemmas in Wordnet '
               "(POS = '{}') ***").format(p)
        PR_scores = wnt.build_wn_PR_scores(p)
        
        # And save them.
        
        print "*** Saving the PR scores to '" + picklefile + "'...",
        ps.save(PR_scores, picklefile)
        print 'OK'
