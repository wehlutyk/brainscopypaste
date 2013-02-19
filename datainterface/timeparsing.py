#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parse and convert strings representing dates and times."""


from __future__ import division

from datetime import datetime
from calendar import timegm


def isostr_to_epoch_mt(isostr):
    """Convert a time-string from the MemeTracker dataset into seconds since
    epoch.

    Parameters
    ----------
    isostr : string
        Representation of a datetime in format ``%Y-%m-%d %H:%M:%S``.

    Returns
    -------
    secs_to_epoch : int
        Number of seconds between epoch and the time represented by `isostr`.

    Raises
    ------
    AssertionError
        If the :class:`datetime.datetime` extracted from `isostr` is
        timezone-aware.

    See Also
    --------
    datetime.datetime

    """

    dt = datetime.strptime(isostr, '%Y-%m-%d %H:%M:%S')
    assert dt.tzinfo is None

    return timegm(dt.utctimetuple())
