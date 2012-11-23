from __future__ import division

import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import networkx as nx

from util import dict_plusone, indices_in_range, list_to_dict, inv_dict
from util.graph import caching_neighbors_walker
import datainterface.picklesaver as ps
from linguistics.treetagger import tagger
import linguistics.wn as l_wn
from analyze.base import AnalysisCase
import settings as st


class Feature(object):

    _cached_instances = {}

    def __init__(self, data_src, ftype, POS):
        self.data_src = data_src
        self.ftype = ftype
        self.POS = POS
        self.fullname = data_src + ' ' + ftype + ' ' + POS
        pre_filename = st.mt_analysis_features[data_src][ftype]['file']
        self.filename = pre_filename.format(POS)
        self.lem = st.mt_analysis_features[data_src][ftype]['lem']
        self.log = st.mt_analysis_features[data_src][ftype]['log']

        self._cache_fnw = {}
        self._cache_fnr = {}

    def __call__(self, key):
        return self.data[key]

    @property
    def values(self):
        try:
            return self._values
        except:
            self.load()
            self._values = np.array(self.data.values())
            return self._values

    def load(self):
        try:
            self.data
        except AttributeError:
            data_raw = ps.load(self.filename)
            self.data = {}
            if self.log:
                for k, v in data_raw.iteritems():
                    self.data[k] = np.log(v)
            else:
                self.data = data_raw

    def features_neighboring_word(self, word, distance):
        try:

            return self._cache_fnw[(word, distance)]

        except KeyError:

            self.load()
            try:
                neighbors = self.walk_neighbors(word, distance)
            except nx.NetworkXError:
                f = None
            else:
                neighbors.discard(word)

                f = []
                for w in neighbors:
                    try:
                        f.append(self.data[w])
                    except KeyError:
                        continue

                if len(f) == 0:
                    f = None
                else:
                    f = np.array(f)

            self._cache_fnw[(word, distance)] = f
            return f

    def mean_feature_neighboring_range(self, f_range, distance):
        try:

            return self._cache_fnr[(f_range, distance)]

        except KeyError:
            self.load()

            idx = indices_in_range(self.values, f_range)
            all_words = self.data.keys()
            words = [all_words[i] for i in idx]

            features = []
            for w in words:
                features_w = self.features_neighboring_word(w, distance)
                if features_w != None:
                    features.extend(features_w)

            if len(features) == 0:
                f = None
            else:
                f = np.array(features).mean()

            self._cache_fnr[(f_range, distance)] = f
            return f

    @classmethod
    def iter_features(cls, aa):

        for s, ts in aa.features.iteritems():

            for t in ts:

                yield cls.get_instance(s, t, aa.POS)

    @classmethod
    def load_G(cls):
        try:

            cls.lem_coords
            cls.inv_coords
            cls.G
            cls.walk_neighbors

        except AttributeError:

            cls.lem_coords, G = l_wn.build_wn_nxgraph()
            cls.inv_coords = inv_dict(cls.lem_coords)
            cls.G = nx.relabel_nodes(G, cls.inv_coords)
            neighbors_walker = caching_neighbors_walker(cls.G)
            def wrapped_neighbors_walker(c, node, distance):
                return neighbors_walker(node, distance)
            cls.walk_neighbors = wrapped_neighbors_walker

    @classmethod
    def get_instance(cls, data_src, ftype, POS):
        cls.load_G()
        try:
            return cls._cached_instances[(data_src, ftype, POS)]
        except KeyError:

            f = Feature(data_src, ftype, POS)
            cls._cached_instances[(data_src, ftype, POS)] = f
            return f


class FeatureAnalysis(AnalysisCase):

    def __init__(self, aa, data, feature):
        super(FeatureAnalysis, self).__init__(aa, data)
        self.feature = feature
        self.log_text = ' [LOG]' if feature.log else ''
        self.nbins = 20
        self.bins = np.linspace(feature.values.min(),
                                feature.values.max(),
                                self.nbins + 1)
        self.bin_middles = (self.bins[1:] + self.bins[:-1]) / 2

        if feature.lem:
            self.w1 = 'lem1'
            self.w2 = 'lem2'
        else:
            self.w1 = 'word1'
            self.w2 = 'word2'

    def analyze(self):
        print 'Analyzing feature ' + self.feature.fullname

        self.feature.load()

        ax = self.fig.add_subplot(221)
        self.plot_variations_from_h0_n(ax)
        #self.plot_mothers_distribution(ax)

        ax = self.fig.add_subplot(222)
        #self.plot_daughters_distribution(ax)
        self.plot_variations_from_h0(ax)

        ax = self.fig.add_subplot(223)
        self.plot_susceptibilities(ax)

        ax = self.fig.add_subplot(224)
        self.plot_variations(ax)

        self.fig.text(0.5, 0.95,
                      self.aa.title() + ' -- ' + self.feature.fullname,
                      ha='center')

    def savefile_postfix(self):
        return self.feature.fullname

    def _plot_distribution(self, ax, values):
        ax.hist(values, bins=self.bins, normed=True,
                log=self.feature.log)
        kde = gaussian_kde(values)
        x = np.linspace(self.bins[0], self.bins[-1], 100)
        ax.plot(x, kde(x), 'g')

    def plot_mothers_distribution(self, ax):
        self.build_l2_f_lists()

        self._plot_distribution(ax, self.l2_f_mothers)

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('# mothers' + self.log_text)

    def plot_daughters_distribution(self, ax):
        self.build_l2_f_lists()

        self._plot_distribution(ax, self.l2_f_daughters)

        ax.set_xlabel('Daughter feature')
        ax.set_ylabel('# daughters' + self.log_text)

    def plot_susceptibilities(self, ax):
        self.build_susceptibilities()

        # Set the backdrop
        patches = ax.hist(self.feature.values, self.bins, normed=True,
                          log=self.feature.log)[2]

        # Get susceptibility of each bin
        binned_suscepts = np.zeros(self.nbins)
        for i in range(self.nbins):
            idx = indices_in_range(self.f_susceptibilities[:, 0],
                                   (self.bins[i], self.bins[i + 1]))
            binned_suscepts[i] = (self.f_susceptibilities[idx, 1].mean()
                                  if len(idx) > 0 else 0)

        # Normalize and set the colors
        b_s_min = binned_suscepts.min()
        b_s_max = binned_suscepts.max()
        binned_suscepts_n = (binned_suscepts - b_s_min) / (b_s_max - b_s_min)
        cmap = cm.YlGnBu
        for i in range(self.nbins):
            patches[i].set_color(cmap(binned_suscepts_n[i]))

        # Add a colorbar
        sm = cm.ScalarMappable(Normalize(b_s_min, b_s_max), cmap)
        sm.set_array(binned_suscepts)
        self.fig.colorbar(sm, ax=ax)

        ax.set_xlabel('Pool feature')
        ax.set_ylabel('Susceptibilities in color' + self.log_text)

    def plot_variations(self, ax):
        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')
        ax.plot(self.bin_middles, self.v_d_h0, 'r', label='h0')
        ax.plot(self.bin_middles, self.v_d_h0_n, 'c', label='h0_n')
        t = '<f(daughter) - f(mother)>'
        ax.plot(self.bin_middles, self.v_d, 'b', linewidth=2, label=t)
        ax.plot(self.bin_middles, self.v_d - self.v_d_std, 'm', label='IC-95%')
        ax.plot(self.bin_middles, self.v_d + self.v_d_std, 'm')

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from mother' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def plot_variations_from_h0(self, ax):
        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')
        t = '<f(daughter)> - <f(daughter)>_h0'
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0,
                'b', linewidth=2, label=t)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0 - self.daughter_d_std,
                'm', label='IC-95%')
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0 + self.daughter_d_std,
                'm')

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from h0' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def plot_variations_from_h0_n(self, ax):
        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')
        t = '<f(daughter)> - <f(daughter)>_h0_n'
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n,
                'b', linewidth=2, label=t)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n - self.daughter_d_std,
                'm', label='IC-95%')
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n + self.daughter_d_std,
                'm')

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from h0_n' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def build_h0(self):
        try:

            self.daughter_d_h0
            self.daughter_d_h0_n
            self.v_d_h0
            self.v_d_h0_n

        except AttributeError:

            self.daughter_d_h0 = np.zeros(self.nbins)
            self.daughter_d_h0_n = np.zeros(self.nbins)
            self.v_d_h0 = np.zeros(self.nbins)
            self.v_d_h0_n = np.zeros(self.nbins)

            for i in range(self.nbins):
                bin_ = (float(self.bins[i]), float(self.bins[i + 1]))

                neighbors_feature = self.feature.mean_feature_neighboring_range(bin_, 2)
                idx = indices_in_range(self.feature.values, bin_)

                if len(idx) > 0:
                    if neighbors_feature != None:
                        self.daughter_d_h0_n[i] = neighbors_feature
                        self.v_d_h0_n[i] = (neighbors_feature
                                            - self.feature.values[idx].mean())
                    else:
                        self.daughter_d_h0_n[i] = None
                        self.v_d_h0_n[i] = None

                    self.daughter_d_h0[i] = self.feature.values.mean()
                    self.v_d_h0[i] = (self.feature.values.mean()
                                      - self.feature.values[idx].mean())
                else:
                    self.daughter_d_h0[i] = None
                    self.daughter_d_h0_n[i] = None
                    self.v_d_h0[i] = None
                    self.v_d_h0_n[i] = None

    def build_variations(self):
        try:

            self.daughter_d
            self.daughter_d_std
            self.v_d
            self.v_d_std

        except AttributeError:

            self.build_l2_f_lists()

            self.daughter_d = np.zeros(self.nbins)
            self.daughter_d_std = np.zeros(self.nbins)
            self.v_d = np.zeros(self.nbins)
            self.v_d_std = np.zeros(self.nbins)

            for i in range(self.nbins):
                bin_ = (self.bins[i], self.bins[i + 1])

                idx = indices_in_range(self.l2_f_mothers, bin_)

                # We need > 1 here to make sure the std computing works
                if len(idx) > 1:

                    daughter_dd = self.l2_f_daughters[idx]
                    self.daughter_d[i] = daughter_dd.mean()
                    self.daughter_d_std[i] = 1.96 * daughter_dd.std() / np.sqrt(len(idx) - 1)

                    v_dd = (self.l2_f_daughters[idx]
                            - self.l2_f_mothers[idx])
                    self.v_d[i] = v_dd.mean()
                    self.v_d_std[i] = 1.96 * v_dd.std() / np.sqrt(len(idx) - 1)

                else:

                    self.daughter_d[i] = None
                    self.daughter_d_std[i] = None

                    self.v_d[i] = None
                    self.v_d_std[i] = None

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

            # Sort by feature value for future use
            self.f_susceptibilities = np.array(self.f_susceptibilities)
            o = np.argsort(self.f_susceptibilities[:,0])
            self.f_susceptibilities = self.f_susceptibilities[o]

    def build_l2_f_cl_ids(self):
        try:
            self.l2_f_cl_ids
        except AttributeError:
            self.l2_f_cl_ids = list_to_dict(self.f_cl_ids)

    def l2_values(self, l1_values):
        l2_values = []

        for idx in self.l2_f_cl_ids.itervalues():
            l2_values.append(l1_values[idx].mean())

        return np.array(l2_values)

    def build_w_lists(self):
        try:

            self.mothers
            self.daughters
            self.cl_ids

        except AttributeError:

            self.mothers = [s[self.w1] for s in self.data]
            self.daughters = [s[self.w2] for s in self.data]
            self.cl_ids = [s.mother.cl_id for s in self.data]

    def build_f_lists(self):
        try:

            self.f_mothers
            self.f_daughters
            self.f_cl_ids

        except AttributeError:

            self.build_w_lists()
            self.f_mothers = []
            self.f_daughters = []
            self.f_cl_ids = []

            for m, d, cl_id in zip(self.mothers, self.daughters, self.cl_ids):

                try:
                    f_m = self.feature(m)
                    f_d = self.feature(d)
                except KeyError:
                    continue

                self.f_mothers.append(f_m)
                self.f_daughters.append(f_d)
                self.f_cl_ids.append(cl_id)

            self.f_mothers = np.array(self.f_mothers)
            self.f_daughters = np.array(self.f_daughters)
            self.f_cl_ids = np.array(self.f_cl_ids)

    def build_l2_f_lists(self):
        try:

            self.l2_f_mothers
            self.l2_f_daughters

        except AttributeError:

            self.build_f_lists()
            self.build_l2_f_cl_ids()

            self.l2_f_mothers = self.l2_values(self.f_mothers)
            self.l2_f_daughters = self.l2_values(self.f_daughters)
            self.l2_f_mothers = self.l2_values(self.f_mothers)
            self.l2_f_daughters = self.l2_values(self.f_daughters)
