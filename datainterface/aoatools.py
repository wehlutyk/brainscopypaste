#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load Age-of-Acquisition data from csv files.

Methods:
* load_aoa_Kuperman_csv: load the AoA Kuperman csv data into a dict

"""


from __future__ import division

import csv

import settings as st


def load_aoa_Kuperman_csv():
    """Load the AoA Kuperman csv data into a dict."""

    aoas = {}
    with open(st.aoa_Kuperman_csv, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        reader.next()
        for row in reader:
            try:
                aoas[row[0]] = float(row[3])
            except:
                pass

    return aoas
