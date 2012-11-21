import datainterface.picklesaver as ps
from analyze.base import AnalysisCase
import settings as st


class Feature(object):

    _cached_instances = {}

    def __init__(self, data_src, ftype):
        self.data_src = data_src
        self.ftype = ftype
        self.fullname = data_src + ' ' + ftype
        self.filename = st.mt_analysis_features[data_src][ftype]['file']
        self.lem = st.mt_analysis_features[data_src][ftype]['lem']

    def load(self):
        self.data = ps.load(self.filename)

    @classmethod
    def iter_features(cls):

        for data_src, ftypes in st.mt_analysis_features.iteritems():

            for ftype in ftypes.iterkeys():

                yield cls.get_instance(data_src, ftype)

    @classmethod
    def get_instance(cls, data_src, ftype):
        try:
            return cls._cached_instances[data_src][ftype]
        except KeyError:

            f = Feature(data_src, ftype)
            try:
                cls._cached_instances[data_src][ftype] = f
            except KeyError:
                cls._cached_instances[data_src] = {}
                cls._cached_instances[data_src][ftype] = f

            return f

class FeatureAnalysis(AnalysisCase):

    def __init__(self, data, feature):
        super(FeatureAnalysis, self).__init__(data)
        self.feature = feature

    def analyze(self):
        pass

