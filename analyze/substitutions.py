import datainterface.picklesaver as ps
from datainterface.fs import get_filename
from features import Feature, FeatureAnalysis
from positions import PositionAnalysis


class SubstitutionsAnalyzer(object):

    def __init__(self, aa):
        self.aa = aa
        self.filename = get_filename(aa)

    def load_analysis_cases(self):
        print 'Loading analysis cases...',

        self.analyses = []

        for feature in Feature.iter_features():
            analysis = FeatureAnalysis(self.substitutions, feature)
            self.analyses.append(analysis)

        analysis = PositionAnalysis(self.substitutions)
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
