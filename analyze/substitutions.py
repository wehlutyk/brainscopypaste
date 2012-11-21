from analyze.base import AnalysisCase

class FeatureAnalysis(AnalysisCase):
    pass

class PositionAnalysis(AnalysisCase):
    pass

class SubstitutionsAnalyzer(object):

    def __init__(self, aa):
        self.aa = aa
