#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Umbrella classes used to perform any kind of analysis on substitutions.

The classes here use all the classes in :mod:`.features`, :mod:`.paths`, and
:mod:`.positions` depending on the arguments they receive. The arguments define
what kind of analysis is to be performed (and if it saved to a file), which in
turn determines the analysis classes and the look of the graphs produced.

"""


from __future__ import division

import re

import pylab as pl

import datainterface.picklesaver as ps
from datainterface.fs import get_filename, check_file, get_fileprefix
from features import Feature, FeatureAnalysis
from positions import PositionsAnalysis
from paths import WNPathsAnalysis, FAPathsAnalysis
import settings as st


class SubstitutionsAnalyzer(object):

    """Analyze substitutions mined with a given set of arguments.

    This class is instantiated whenever a set of substitutions is to be
    analyzed. Given command line arguments, it automatically loads the
    previously mined substitutions corresponding to the provided arguments, and
    performs the analysis specified in the arguments.

    Parameters
    ----------
    aa : :class:`.args.AnalysisArgs` instance
        The analysis arguments to use.

    Attributes
    ----------
    aa : :class:`.args.AnalysisArgs` instance
        The analysis arguemnts passed to the constructor.
    filename : string
        The filename of the data to be loaded, corresponding to the provided
        analysis args.
    analyses : list of :class:`.base.AnalysisCase` instances
        The analysis cases to perform.
    substitutions : list of :class:`mine.substitutions.Substitution`
        The substitution list loaded from `filename`.

    See Also
    --------
    .args.AnalysisArgs, SubstitutionsGroupAnalyzer

    """

    def __init__(self, aa):
        """Initialize the structure from analysis arguments and preload the
        data.

        Parameters
        ----------
        aa : :class:`.args.AnalysisArgs` instance
            The analysis arguments to use.

        See Also
        --------
        preload

        """

        self.aa = aa
        self.filename = get_filename(aa)
        check_file(self.filename, for_read=True)
        self.preload()

    def preload(self):
        """Load analysis cases and substitutions from file, if not already
        done.

        The analysis cases are stored in `self.analyses`, and the substitutions
        are stored in `self.substitutions`. If these were already previously
        loaded, nothing is done.

        See Also
        --------
        load_analysis_cases, load_substitutions

        """

        try:
            # Have we already loaded these? If so, do nothing
            self.analyses
            self.substitutions

        except AttributeError:

            self.load_substitutions()
            self.load_analysis_cases()

    def load_analysis_cases(self):
        """Load analysis cases according to the analysis args.

        The analysis cases are stored in `self.analyses`. They can be feature-,
        positions-, or paths-analysis, and are included in the final list
        depending on the analyis arguments.

        """

        print 'Loading analysis cases...',

        self.analyses = []

        for feature in Feature.iter_features(self.aa):
            analysis = FeatureAnalysis(self.aa, self.substitutions, feature)
            self.analyses.append(analysis)

        if self.aa.positions:
            analysis = PositionsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        if self.aa.paths:
            analysis = WNPathsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)
            analysis = FAPathsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        print 'OK'

    def load_substitutions(self):
        """Load previously mined substitutions from file.

        The loaded substitutions are stored in `self.substitutions`.

        """

        print 'Loading substitutions...',
        self.substitutions = ps.load(self.filename)
        print 'OK'

    def analyze(self, axss, filepaths):
        """Perform the analyses asked for by the analysis args.

        The analysis parameters are first printed to stdout, then each analysis
        in `self.analyses` is run.

        See Also
        --------
        .base.AnalysisCase

        """

        self.aa.print_analysis()

        saves = []
        print 'Running analyses...'
        for a, axs, filepath in zip(self.analyses, axss, filepaths):
            saves.append(a.analyze(axs, filepath))
        return saves


class SubstitutionsGroupAnalyzer(object):

    """Analyze substitution lists with figure grouping.

    When trying to compare the effect of analysis or mining arguments, it can
    be useful to plot the feature-, path-, or position-analysis for different
    arguments on the *same* figure (or set of axes). This class enables this.
    It reads a set of grouped analysis arguments, telling it which analysis
    arguments are to be grouped in the same figures. It performs the analyses
    specified in the individual analysis arguments, stacking the graphs for
    different analysis arguments into the same figure (but we still have
    different figures for different analysis cases).

    Parameters
    ----------
    gaa : :class:`.args.GroupAnalysisArgs` instance
        The grouped analysis args to analyze for.

    Attributes
    ----------
    gaa : :class:`.args.GroupAnalysisArgs` instance
        The grouped analysis args passed to the constructor.
    base_savefile_prefix : string
        The prefix to be used when saving graphs to file.

    See Also
    --------
    .args.GroupAnalysisArgs, .args.MultipleAnalysisArgs

    """

    def __init__(self, gaa):
        """Initialize the structure according to provided grouped analysis
        args.

        Parameters
        ----------
        gaa : :class:`.args.GroupAnalysisArgs` instance
            The grouped analysis args to analyze for.

        """

        self.gaa = gaa
        self.base_savefile_prefix = get_fileprefix(gaa)

    def build_analysis_cases_attrs(self, sa):
        """Build the set of figures and axes onto which all anlyses will
        be stacked.

        This method takes a :class:`SubstitutionsAnalyzer` instance as
        parameter, and uses it as a prototype to create the set of figures,
        axes, and savefiles into which the analysis will be plotted and
        possibly saved. Any substitutions analyzer created from analysis args
        in `self.gaa` will do, since they should all generate the same sets of
        figures/axes/savefiles. The generated figures/axes/savefiles are then
        repeatedly used in :meth:`analyze` to plot the analyses.

        The created figures are stored in `self.figs`, the created list of
        lists of axes are in `self.axss`, and the created file paths for
        possible saving are in `self.filepaths`.

        Parameters
        ----------
        sa : :class:`SubstitutionsAnalyzer` instance
            The substitutions analyzer used to created the set of figures.

        See Also
        --------
        SubstitutionsAnalyzer, .base.AnalysisCase

        """

        self.figs = []
        self.axss = []
        self.filepaths = []
        for a in sa.analyses:
            self.figs.append(pl.figure())
            self.axss.append(a.build_axes(self.figs[-1]))
            filename = (self.base_savefile_prefix +
                        re.sub(' ', '-', a.savefile_postfix()))
            self.filepaths.append(st.mt_analysis_figure_file.format(filename))

    def analyze(self):
        """Perform the analyses and stack them on a single set of figures for
        all the analysis args in `self.gaa`.

        See Also
        --------
        SubstitutionsAnalyzer

        """

        print
        print "*** New set of figures"

        # Run the analyses
        for aa in self.gaa:
            sa = SubstitutionsAnalyzer(aa)
            # If we haven't yet created the set of axes, figures, and
            # savefiles onto which to stack the analyses, do it now
            try:
                self.figs
                self.axss
                self.filepaths
            except AttributeError:
                self.build_analysis_cases_attrs(sa)
            # The saves list should be the same for each aa.
            # Here we're keeping the last one (we could take any).
            saves = sa.analyze(self.axss, self.filepaths)

        # Print titles
        for a, fig in zip(sa.analyses, self.figs):
            a.print_fig_text(fig, self.gaa.title())

        # Save if asked to
        if self.gaa.save:
            for save, fig, filepath in zip(saves, self.figs, self.filepaths):
                if save:
                    fig.canvas.print_figure(filepath, dpi=300)

    @classmethod
    def analyze_multiple(cls, maa):
        """Perform grouped analyses for multiple group analysis args.

        The kind of analysis performed by this
        :class:`SubstitutionsGroupAnalyzer` can be useful to iterate over, with
        different sets of grouped analysis args. This method allows for that.
        It iterates over the grouped analysis args and performs a grouped
        substitution analysis for each, creating a new
        :class:`SubstitutionsGroupAnalyzer` each time.

        Parameters
        ----------
        maa : :class:`.args.MultipleAnalysisArgs` instance
            The multpile analysis args able to create
            :class:`.args.GroupAnalysisArgs` instances when iterated over.

        See Also
        --------
        .args.MultipleAnalysisArgs

        """

        maa.print_analysis()

        for gaa in maa:
            sga = cls(gaa)
            sga.analyze()
