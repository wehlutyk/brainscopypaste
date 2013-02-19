from __future__ import division

import numpy as np
import networkx as nx

import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import linguistics.fa as l_fa
from util.generic import inv_dict
from analyze.base import AnalysisCase
import settings as st


class BasePathsAnalysis(AnalysisCase):

    def __init__(self, aa, data):
        super(BasePathsAnalysis, self).__init__(aa, data)

    def savefile_postfix(self):
        raise NotImplementedError

    def load(self):
        try:

            self.distribution
            self.lem_coords
            self.inv_coords
            self.G

        except AttributeError:

            print 'Loading path data'
            self.distribution = ps.load(self.filename)
            self.lem_coords, G = self.load_graph()
            self.inv_coords = inv_dict(self.lem_coords)
            self.G = nx.relabel_nodes(G, self.inv_coords)

    def build_lengths(self):
        self.load()
        try:

            self.lengths
            self.bins
            self.n_lengths

        except AttributeError:

            self.lengths = []
            for s in self.data:
                try:
                    l = nx.shortest_path_length(self.G, s.lem1, s.lem2)
                    self.lengths.append(l)
                except (nx.NetworkXError, nx.NetworkXNoPath):
                    continue

            self.lengths = np.array(self.lengths)
            l_min = self.lengths.min()
            l_max = self.lengths.max()
            self.bins = np.arange(l_min, l_max + 2) - 0.5
            self.x = np.arange(l_min, l_max + 1, dtype=int)
            self.n_lengths = np.histogram(self.lengths, bins=self.bins,
                                          normed=True)[0]

    def analyze_inner(self):
        print 'Analyzing paths'

        self.build_lengths()

        ax = self.fig.add_subplot(211)
        self.plot_observed(ax)

        ax = self.fig.add_subplot(212)
        self.plot_normalized_observed(ax)

        self.fig.text(0.5, 0.95,
                      self.latexize(self.aa.title() + ' --- '
                                    + self.savefile_postfix()),
                      ha='center')

    def plot_observed(self, ax):
        ax.plot(self.x, self.n_lengths, 'b', label='Observed')
        ax.set_xlabel('Distance')
        ax.set_ylabel('Probability density')
        ax.legend(loc='best')

    def plot_normalized_observed(self, ax):
        c_distribution = self.distribution[self.x]
        ax.plot(self.x, self.n_lengths / c_distribution,
                'r', label='Normalized observed')
        ax.set_xlabel('Distance')
        ax.legend(loc='best')


class WNPathsAnalysis(BasePathsAnalysis):

    def __init__(self, aa, data):
        super(WNPathsAnalysis, self).__init__(aa, data)
        self.filename = st.wn_lengths_pickle
        self.load_graph = l_wn.build_wn_nxgraph

    def savefile_postfix(self):
        return 'paths-wn'


class FAPathsAnalysis(BasePathsAnalysis):

    def __init__(self, aa, data):
        super(FAPathsAnalysis, self).__init__(aa, data)
        self.filename = st.fa_lengths_pickle
        self.load_graph = l_fa.build_fa_nxgraph

    def savefile_postfix(self):
        return 'paths-fa'
