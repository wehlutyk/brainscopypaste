#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Store data from datasets in well-formed structures, with an object-oriented interface for accessing the data.

Modules defined here define the core objects used to represent the data, and used in the analysis. Each module defines
a number of objects relevant to its dataset. Each object first has a number of base methods used by other packages, then
uses the methods defined in other analysis packages to give an object-oriented interface to the data. As an example, the
visualize package defines methods to plot data from the MemeTracker dataset, and the Cluster and Quote object in the
memetracker module here define methods that wrap those visualization methods.

Modules:
  * memetracker: hold data from the MemeTracker dataset: Clusters, Quotes, Timelines, and TimeBags

"""
