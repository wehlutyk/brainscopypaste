#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load Age-of-Acquisition data from csv files."""


from __future__ import division

import csv

import settings as st


def load_aoa_Kuperman_csv():
    """Load the AoA Kuperman csv data into a dict.

    The path to the csv file is taken from the
    :const:`settings.aoa_Kuperman_csv` variable.

    Returns
    -------
    aoas : dict
        Mapping of ``word, AoA`` couples (words in lowercase).

    """

    aoas = {}
    with open(st.aoa_Kuperman_csv, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        reader.next()
        for row in reader:
            try:
                aoas[row[0]] = float(row[3])
            except ValueError:
                pass

    return aoas
