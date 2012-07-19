#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parse and convert strings representing dates and times.

Methods:
  * isostr_to_epoch_linkfluence: convert a time-string from the Linkfluence
                                 dataset into seconds since epoch
  * isostr_to_epoch_mt: convert a time-string from the MemeTracker dataset
                        into seconds since epoch

"""


from __future__ import division

from datetime import timedelta, datetime
from calendar import timegm
import re

from pylab import sign


# Module code
def isostr_to_epoch_linkfluence(isostr):
    """Convert a time-string from the Linkfluence dataset into seconds since
    epoch.

    Arguments:
      * isostr: a string in format '%Y-%m-%dT%H:%M:%SZ'
                                or '%Y-%m-%dT%H:%M:%S+%Hz:%Mz'
                                or '%Y-%m-%dT%H:%M:%S-%Hz:%Mz'

    Returns: the number of seconds between epoch and the time represented by
             'isostr'.

    """

    # Convert any potential 'Z' to '+00:00'.

    tzisostr = re.sub(r'Z$', '+00:00', isostr)

    # Get the timezone offset and strip it from the 'tzisostr'.

#    try:

    if len(tzisostr) >= 20:

        tzoffset = int(tzisostr[-6:-3])
        offsetstr = tzisostr[:-6]

    else:

        tzoffset = 0
        offsetstr = tzisostr

#    except:
#
#        print 'Exception caught in int()'
#        print 'isostr =', isostr

    # Convert the offsetstr to a datetime.

    offsetdt = datetime.strptime(offsetstr, '%Y-%m-%dT%H:%M:%S')

    # Correct the offsetdt by the tzoffset.

    utcdt = offsetdt - sign(tzoffset) * timedelta(hours=tzoffset)
    assert utcdt.tzinfo is None

    # Finally, return the number of seconds since epoch.

    return timegm(utcdt.utctimetuple())


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
