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

import linguistics.memetracker as l_mt
import analyze.memetracker as a_mt
import visualize.memetracker as v_mt


class Timeline(v_mt.TimelineVisualize):

    pass


class Quote(v_mt.QuoteVisualize):

    pass


class Cluster(a_mt.ClusterAnalyze,v_mt.ClusterVisualize,
              l_mt.ClusterLinguistics):

    pass


class QtString(l_mt.QtStringLinguistics):

    pass


class TimeBag(l_mt.TimeBagLinguistics):

    pass


