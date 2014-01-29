#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get the number of phonemes for each word in CMU and store that
dict in a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.cmu as l_cmu
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the number of phonemes

    picklefile = st.cmu_MNphonemes_pickle
    try:
        di_fs.check_file(picklefile)
    except Exception:

        print
        print "The MNphonemes data already exists."
        print "Nothing to do. Exiting."

    else:

        print
        print "*** Loading MNphonemes from CMU ***"
        MNphonemes = l_cmu.get_all_MNphonemes()

        print "*** Saving the MNphonemes to '" + picklefile + "'...",
        ps.save(MNphonemes, picklefile)
        print "OK"
