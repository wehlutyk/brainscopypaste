import datainterface.picklesaver as ps
from datainterface.fs import get_filename
from features import Feature, FeatureAnalysis
from positions import PositionAnalysis
from paths import PathsAnalysis

class SubstitutionsAnalyzer(object):

    def __init__(self, aa):
        self.aa = aa
        self.filename = get_filename(aa)

    def load_analysis_cases(self):
        print 'Loading analysis cases...',

        self.analyses = []

        for feature in Feature.iter_features(self.aa):
            analysis = FeatureAnalysis(self.aa, self.substitutions, feature)
            self.analyses.append(analysis)

        if self.aa.positions:
            analysis = PositionAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        if self.aa.paths:
            analysis = PathsAnalysis(self.aa, self.substitutions)
            self.analyses.append(analysis)

        print 'OK'

    def load_substitutions(self):
        print 'Loading substitutions...',
        self.substitutions = ps.load(self.filename)
        print 'OK'

    def analyze(self):
        self.aa.print_analysis()
        self.load_substitutions()
        self.load_analysis_cases()

        print 'Running analyses...'
        for a in self.analyses:
            a.analyze()

    @classmethod
    def analyze_multiple(cls, maa):
        maa.print_analysis()

        for aa in maa:
            sa = cls(aa)
            sa.analyze()
