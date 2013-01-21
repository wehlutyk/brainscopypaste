import re

import pylab as pl

import datainterface.picklesaver as ps
from datainterface.fs import get_filename, check_file, get_fileprefix
from features import Feature, FeatureAnalysis
from positions import PositionsAnalysis
from paths import PathsAnalysis
import settings as st


class SubstitutionsAnalyzer(object):

    def __init__(self, aa):
        self.aa = aa
        self.filename = get_filename(aa)
        check_file(self.filename, for_read=True)
        self.preload()

    def preload(self):
        try:

            self.analyses
            self.substitutions

        except AttributeError:

            self.load_substitutions()
            self.load_analysis_cases()

    def load_analysis_cases(self):
        print 'Loading analysis cases...',

        self.analyses = []

        for feature in Feature.iter_features(self.aa):
            analysis = FeatureAnalysis(self.aa, self.substitutions, feature)
            self.analyses.append(analysis)

        if self.aa.positions:
            analysis = PositionsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        if self.aa.paths:
            analysis = PathsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        print 'OK'

    def load_substitutions(self):
        print 'Loading substitutions...',
        self.substitutions = ps.load(self.filename)
        print 'OK'

    def analyze(self, axss, filepaths):
        self.aa.print_analysis()

        saves = []
        print 'Running analyses...'
        for a, axs, filepath in zip(self.analyses, axss, filepaths):
            saves.append(a.analyze(axs, filepath))
        return saves


class SubstitutionsGroupAnalyzer(object):

    def __init__(self, gaa):
        self.gaa = gaa
        self.base_savefile_prefix = get_fileprefix(gaa)

    def build_analysis_cases_attrs(self, sa):
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
        print
        print "*** New set of figures"

        # Run the analyses
        for aa in self.gaa:
            sa = SubstitutionsAnalyzer(aa)
            try:
                self.figs
                self.axss
                self.filepaths
            except AttributeError:
                self.build_analysis_cases_attrs(sa)
            # The saves list should be the same for each aa
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
        maa.print_analysis()

        for gaa in maa:
            sga = cls(gaa)
            sga.analyze()
