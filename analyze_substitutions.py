#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze a set of previously mined substitutions, defined by a set of
:class:`analyze.args.AnalysisArgs`.

This script is meant to be used as a command line program. It will load
previously mined substitutions from pickle files (mined with
:mod:`mine_substitutions` or :mod:`mine_substitutions_multiple`) according to
its arguments, and plot various visualizations of those substitutions depending
on its arguments.

Run ``python analyze_substitutions.py --help`` for more details on the
arguments.

"""


from __future__ import division

import pylab as pl

from analyze.args import AnalysisArgs
from analyze.substitutions import SubstitutionsAnalyzer


if __name__ == '__main__':
    analysis_args = AnalysisArgs()
    sa = SubstitutionsAnalyzer(analysis_args)
    sa.analyze()

    if analysis_args.show:
        pl.show()
