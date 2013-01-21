import datainterface.picklesaver as ps
from datainterface.fs import get_filename, check_file
from features import Feature, FeatureAnalysis
from positions import PositionsAnalysis
from paths import PathsAnalysis


class SubstitutionsAnalyzer(object):

    def __init__(self, aa):
        self.aa = aa
        self.filename = get_filename(aa)
        check_file(self.filename, for_read=True)

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

        for aas in maa:
            print
            print 'Graph ------------------------'
            for aa in aas:
                aa.print_analysis()
            #sa = cls(aa)
            #sa.analyze()
