#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load the Age-of-Acquisition data from the Kuperman csv file into
a dict, and save that in a pickle file."""


import datainterface.picklesaver as ps
import datainterface.aoatools as at
import settings as st


if __name__ == '__main__':

    # Load or compute the AoA data

    picklefile = st.aoa_Kuperman_pickle
    try:
        st.check_file(picklefile)
    except Exception:

        print
        print "The AoA data already exists."
        print "Nothing to do. Exiting."

    else:

        print
        print "*** Loading AoA Kuperman data from csv ***"
        aoa_Kuperman = at.load_aoa_Kuperman_csv()

        print "*** Saving the AoA Kuperman data to '" + picklefile + "'...",
        ps.save(aoa_Kuperman, picklefile)
        print "OK"
