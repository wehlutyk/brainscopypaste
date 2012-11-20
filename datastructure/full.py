#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hold data from the MemeTracker dataset like Clusters, Quotes, Timelines,
and TimeBags.

Classes:
  * Timeline: hold a series of occurences (e.g. occurences of a quote, or of
              quotes related to a same cluster)
  * Quote: hold a quote, its attributes, and its timeline (this is a subclass
           of Timeline)
  * Cluster: hold a cluster, its attributes, its quotes, and if necessary its
             Timeline
  * QtString: augment a string with POS tags, tokens, cluster id and quote id
  * TimeBag: a bag of strings with some attributes, resulting from the
             splitting of a Cluster (or Quote) into time windows

"""

import mine.models as m_mo
import visualize.mt as v_mt


class Timeline(v_mt.TimelineVisualize):

    pass


class Quote(v_mt.QuoteVisualize,m_mo.QuoteModels):

    pass


class Cluster(m_mo.ClusterModels,v_mt.ClusterVisualize):

    pass


class QtString(m_mo.QtStringModels):

    pass


class TimeBag(m_mo.TimeBagModels):

    pass


