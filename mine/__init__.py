#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mine for substitutions in the dataset, with different sets of arguments.

Substitutions mining is a tricky art. It takes filtering, lemmatizing,
grammatical tagging, substring analysis, multithreading, and source-destination
modelling to make a good substitution miner.

The :mod:`.args` module lets you define the way in which you combine all those
subtools to mine your substitutions. The :mod:`.filters` module lets you sift
through the cluster data before starting to mine, shaping and filtering your
clusters to your needs. The :mod:`.models` module defines the different ways
you can reconstruct the source-destination information which isn't present in
the cluster data. The :mod:`.substitutions` brings all of these tools together
to do the actual mining. Finally, the :mod:`.statistics` module lets you get an
overview of some aspects of the cluster data, just a peak before diving in.

"""
