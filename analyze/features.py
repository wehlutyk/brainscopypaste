from __future__ import division

import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import Normalize

from util import dict_plusone
import datainterface.picklesaver as ps
from linguistics.treetagger import tagger
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

    def __call__(self, key):
        return self.data[key]

    def values(self):
        return np.array(self.data.values())

    def load(self):
        try:
            self.data
        except AttributeError:
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

        if feature.lem:
            self.w1 = 'lem1'
            self.w2 = 'lem2'
        else:
            self.w1 = 'word1'
            self.w2 = 'word2'

    def analyze(self):
        self.feature.load()
        self.build_l2_f_lists()

    def plot_mothers_distribution(self, ax):
        self.build_l2_f_lists()

        ax.hist(self.l2_f_mothers, log=True)

        ax.set_title('Mothers distribution')
        ax.set_xlabel(self.feature.fullname)
        ax.set_ylabel('# mothers')
        ax.legend()

    def plot_daughters_distribution(self, ax):
        self.build_l2_f_lists()

        ax.hist(self.l2_f_daughters, log=True)

        ax.set_title('Daughters distribution')
        ax.set_xlabel(self.feature.fullname)
        ax.set_ylabel('# daughters')
        ax.legend()

    def plot_susceptibilities(self, ax):
        self.build_susceptibilities()

        # Set the backdrop
        bins, patches = ax.hist(self.feature.values(), log=True)[1:]
        nbins = len(bins) - 1

        # Get susceptibility of each bin
        binned_suscepts = np.zeros(nbins)
        for i in range(nbins):
            idx = np.where((bins[i] <= self.f_susceptibilities[:,0])
                           * (self.f_susceptibilities[:,0] < bins[i+1]))[0]
            binned_suscepts[i] = self.f_susceptibilities[idx].mean()

        # Normalize and set the colors
        binned_suscepts_n = ((binned_suscepts - binned_suscepts.min()) /
                             (binned_suscepts.max() - binned_suscepts.min()))
        cmap = cm.YlGnBu
        for i in range(nbins):
            patches[i].set_color(cmap(binned_suscepts_n[i]))

        # Add a colorbar
        sm = cm.ScalarMappable(Normalize(binned_suscepts.min(), binned_suscepts.max()), cmap)
        sm.set_array(binned_suscepts)
        self.fig.colorbar(sm, ax=ax)

        ax.set_title('Susceptibilities on feature distribution')
        ax.set_xlabel(self.feature.fullname)
        ax.set_ylabel('Feature distribution')
        ax.legend()

    def build_susceptibilities(self):
        try:

            self.f_susceptibilities

        except AttributeError:

            possibilities = {}
            realizations = {}

            for s in self.data:

                # Lemmatize if asked to
                if self.feature.lem:
                    # This will take advantage of data from
                    # future analyses
                    try:
                        words = s.mother.lems
                    except AttributeError:
                        words = tagger.Lemmatize(s.mother)
                else:
                    words = s.mother.tokens

                # Update possibilities
                for w in words:
                    dict_plusone(possibilities, w)

                # And realizations
                dict_plusone(realizations, s[self.w2])

            # Now compute the susceptibilities
            self.w_susceptibilities = {}
            self.f_susceptibilities = []
            for w, p in possibilities.iteritems():

                # Set susceptibility to zero if there were
                # no realizations
                try:
                    ws = realizations[w] / possibilities[w]
                except KeyError:
                    ws = 0
                self.w_susceptibilities[w] = ws

                # Only store the words which exit in our feature list
                try:
                    self.f_susceptibilities.append([self.feature(w), ws])
                except:
                    pass

            # Sort be feature value for future use
            self.f_susceptibilities = np.array(self.f_susceptibilities)
            o = np.argsort(self.f_susceptibilities[:,0])
            self.f_susceptibilities = self.f_susceptibilities[o]

    def build_w_lists(self):
        try:

            self.mothers
            self.daughters

        except AttributeError:

            self.mothers = [s[self.w1] for s in self.data]
            self.daughters = [s[self.w2] for s in self.data]

    def build_f_lists(self):
        try:

            self.f_mothers
            self.f_daughters

        except AttributeError:

            self.build_w_lists()
            self.f_mothers = []
            self.f_daughters = []

            for m, d in zip(self.mothers, self.daughters):

                try:
                    f_m = self.feature(m)
                    f_d = self.feature(d)
                except KeyError:
                    continue

                self.f_mothers.append(f_m)
                self.f_daughters.append(f_d)

            self.f_mothers = np.array(self.f_mothers)
            self.f_daughters = np.array(self.f_daughters)

    def build_l2_f_lists(self):
        try:

            self.l2_f_mothers
            self.l2_f_daughters

        except AttributeError:

            self.build_f_lists()
            self.build_l2_cl_ids()

            self.l2_f_mothers = self.l2_values(self.f_mothers)
            self.l2_f_daughters = self.l2_values(self.f_daughters)


