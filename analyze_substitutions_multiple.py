#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze multiple sets of previously mined substitutions, defined by a set of
:class:`analyze.args.MultipleAnalysisArgs`.

This script is meant to be used as a command line program. It will load several
sets of previously mined substitutions from pickle files (mined with
:mod:`mine_substitutions` or :mod:`mine_substitutions_multiple`) according to
its arguments, and plot various visualizations of those substitutions depending
on its arguments. Different sets of mining arguments can be combined into
single plots, allowing for easy comparison of the effects of mining arguments
on the results (e.g. source-destination reconstruction model, substrings or POS
handling, etc. -- play around with the ``--ingraph`` option to see this).

Run ``python analyze_substitutions_multiple.py --help`` for more details on the
arguments.

"""


from __future__ import division

import pylab as pl

from analyze.args import MultipleAnalysisArgs
from analyze.substitutions import SubstitutionsGroupAnalyzer


if __name__ == '__main__':

    multiple_analysis_args = MultipleAnalysisArgs()
    SubstitutionsGroupAnalyzer.analyze_multiple(multiple_analysis_args)

    if multiple_analysis_args.show:
        pl.show()
