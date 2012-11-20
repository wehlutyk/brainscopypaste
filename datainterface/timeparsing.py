#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parse and convert strings representing dates and times.

Methods:
  * isostr_to_epoch_mt: convert a time-string from the MemeTracker dataset
                        into seconds since epoch

"""


from __future__ import division

from datetime import datetime
from calendar import timegm


def isostr_to_epoch_mt(isostr):
    """Convert a time-string from the MemeTracker dataset into seconds since
    epoch.

    Arguments:
      * isostr: a string in format '%Y-%m-%d %H:%M:%S'

    Returns: the number of seconds between epoch and the time represented by
             'isostr'.

    """

    dt = datetime.strptime(isostr, '%Y-%m-%d %H:%M:%S')
    assert dt.tzinfo is None

    return timegm(dt.utctimetuple())
