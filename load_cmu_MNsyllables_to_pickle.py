#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get the number of syllables for each word in CMU and store that
dict in a pickle file."""


from __future__ import division

import datainterface.picklesaver as ps
import linguistics.cmu as l_cmu
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the number of syllables

    picklefile = st.cmu_MNsyllables_pickle
    try:
        di_fs.check_file(picklefile)
    except Exception:

        print
        print "The MNsyllables data already exists."
        print "Nothing to do. Exiting."

    else:

        print
        print "*** Loading MNsyllables from CMU ***"
        MNsyllables = l_cmu.get_all_MNsyllables()

        print "*** Saving the MNsyllables to '" + picklefile + "'...",
        ps.save(MNsyllables, picklefile)
        print "OK"
