# -*- coding: utf-8 -*-
'''
Parsing functions for strings representing time
'''


#
# Imports
#
from datetime import timedelta, datetime
from calendar import timegm
from pylab import sign
import re


#
# Module code
#
def isostr_to_epoch(isostr):
    '''
    Takes a string in format '%Y-%m-%dT%H:%M:%SZ'
                          or '%Y-%m-%dT%H:%M:%S+%Hz:%Mz'
                          or '%Y-%m-%dT%H:%M:%S-%Hz:%Mz'
    and converts it to a number of seconds since the epoch
    '''
    
    # Convert the 'Z' to '+00:00'
    tzisostr = re.sub(r'Z$', '+00:00', isostr)
    
    # Get the timezone offset and strip it from the tzisostr
    try:
        if len(tzisostr) >= 20:
            tzoffset = int(tzisostr[-6:-3])
            offsetstr = tzisostr[:-6]
        else:
            tzoffset = 0
            offsetstr = tzisostr
    except:
        print 'Exception caught in int()'
        print 'isostr =', isostr
    
    # Convert the offsetstr to a datetime
    offsetdt = datetime.strptime(offsetstr, '%Y-%m-%dT%H:%M:%S')
    
    # Correct the offsetdt by the tzoffset
    utcdt = offsetdt - sign(tzoffset)*timedelta(hours=tzoffset)
    assert utcdt.tzinfo is None
    
    # Finally, return the number of seconds since epoch
    return timegm(utcdt.utctimetuple())
