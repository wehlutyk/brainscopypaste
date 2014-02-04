#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hold data from the MemeTracker dataset like Clusters, Quotes, Timelines,
and TimeBags."""


from __future__ import division

import mine.models as m_mo
import visualize.mt as v_mt


class Timeline(v_mt.TimelineVisualize):

    """Full timeline object, used for visualization.

    This full class pulls in the
    :class:`~visualize.mt.TimelineVisualize` mixin for visualization.

    See Also
    --------
    .base.TimelineBase, visualize.mt.TimelineVisualize

    """

    pass


class Quote(v_mt.QuoteVisualize, m_mo.QuoteModels):

    """Full quote object, used for analysis and visualization.

    This full class pulls in:

    * The :class:`~mine.models.QuoteModels` mixin for substitution analysis
    * The :class:`~visualize.mt.QuoteVisualize` mixin for visualization

    See Also
    --------
    .base.QuoteBase, mine.models.QuoteModels, visualize.mt.QuoteVisualize

    """

    pass


class Cluster(m_mo.ClusterModels, v_mt.ClusterVisualize):

    """Full cluster object, used for analysis and visualization.

    This full class pulls in:

    * The :class:`~mine.models.ClusterModels` mixin for substitution analysis
    * The :class:`~visualize.mt.ClusterVisualize` mixin for visualization

    See Also
    --------
    .base.ClusterBase, mine.models.ClusterModels, visualize.mt.ClusterVisualize

    """

    pass


class QtString(m_mo.QtStringModels):

    """Full quote-string object, used for analysis.

    This full class pulls in the :class:`~mine.models.QtStringModels` mixin
    for substitution analysis.

    See Also
    --------
    mine.models.QtStringModels

    """

    pass


class TimeBag(m_mo.TimeBagModels):

    """Full timebag object, used for analysis.

    This full class pulls in the :class:`~mine.models.TimeBagModels` mixin
    for substitution analysis.

    See Also
    --------
    .base.TimeBagBase, mine.models.TimeBagModels

    """

    pass
