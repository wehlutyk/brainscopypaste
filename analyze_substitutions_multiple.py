#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pylab as pl

from analyze.args import MultipleAnalysisArgs
from analyze.substitutions import SubstitutionsAnalyzer


if __name__ == '__main__':

    multiple_analysis_args = MultipleAnalysisArgs()
    SubstitutionsAnalyzer.analyze_multiple(multiple_analysis_args)

    if multiple_analysis_args.show:
        pl.show()
