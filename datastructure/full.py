#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hold data from the MemeTracker dataset like Clusters, Quotes, Timelines,
and TimeBags."""


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


