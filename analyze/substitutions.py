import numpy as np

from util import list_to_dict
import datainterface.picklesaver as ps
from datainterface.fs import get_filename
from base import AnalysisCase
from features import Feature, FeatureAnalysis
from positions import PositionAnalysis


class SubstitutionAnalysisCase(AnalysisCase):

    def build_l2_cl_ids(self):
        try:
            self.l2_cl_ids
        except AttributeError:
            self.l2_cl_ids = list_to_dict([s.mother.cl_id for s in self.data])

    def l2_values(self, l1_values):
        l2_values = []

        for idx in self.l2_cl_ids.itervalues():
            l2_values.append(l1_values[idx].mean())

        return np.array(l2_values)


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
