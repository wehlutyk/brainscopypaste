#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for analyzing the distance travelled on graphs upon substitution.

These analysis produce probability densities for the number of hops made on a
graph upon substitution. The graph can be either WordNet or Free Association.

The classes are based on :class:`~.analyze.AnalysisCase`.

"""


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

    """Base class for building a path analysis for substitutions.

    The :class:`WNPathsAnalysis` and :class:`FAPathsAnalysis` are built on this
    class. It provides the common methods used to compute distances on the
    graph and plot number-of-hops distributions.

    Parameters
    ----------
    aa : :class:`AnalysisArgs` instance
        The analysis arguments used for the whole analysis.
    data : list
        The data on which to perform the paths analysis; usually a list of
        :class:`~mine.substitutions.Substitution`\ s.

    See Also
    --------
    WNPathsAnalysis, FAPathsAnalysis, .base.AnalysisCase

    """

    def __init__(self, aa, data):
        """Initialize the structure by deferring to super.

        Parameters
        ----------
        aa : :class:`AnalysisArgs` instance
            The analysis arguments used for the whole analysis.
        data : list
            The data on which to perform the paths analysis; usually a list of
            :class:`~mine.substitutions.Substitution`\ s.

        """

        super(BasePathsAnalysis, self).__init__(aa, data)

    def savefile_postfix(self):
        """Get the postfix to be added to the save file name
        (abstract method)."""

        raise NotImplementedError

    def load(self):
        """Load the graph and precomputed paths data.

        The distribution of distances in the graph is loaded into
        `self.distribution` and the graph itself is loaded into `self.G`. If
        this data was already loaded previously, nothing is done.

        """

        try:
            # Did we alreadu compute these earlier? If so, do nothing
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
        """Compute distances travelled on each substitution.

        The list of path lengths (corresponding to the list of substitutions in
        `self.data`) is stored in `self.lengths`, the bins for the histogram
        are stored in `self.bins`, the corresponding bin middles are stored in
        `self.x`, and the distribution corresponding to these bins is stored in
        `self.n_lengths`. If those values were already computed previously,
        nothing is done.

        See Also
        --------
        load

        """

        # Make sure we have the graph data loaded first
        self.load()

        try:
            # Did we alreadu compute these earlier? If so, do nothing
            self.lengths
            self.bins
            self.x
            self.n_lengths

        except AttributeError:

            self.lengths = []
            for s in self.data:
                # Skip silently if lem1 or lem2 don't exist in the graph,
                # or if there is no path from lem1 to lem2.
                try:
                    # We always take lemmatized words here.
                    l = nx.shortest_path_length(self.G, s.lem1, s.lem2)
                    self.lengths.append(l)
                except (nx.NetworkXError, nx.NetworkXNoPath):
                    continue

            # Cast into numpy arrays and compute distribution
            self.lengths = np.array(self.lengths)
            l_min = self.lengths.min()
            l_max = self.lengths.max()
            self.bins = np.arange(l_min, l_max + 2) - 0.5
            self.x = np.arange(l_min, l_max + 1, dtype=int)
            self.n_lengths = np.histogram(self.lengths, bins=self.bins,
                                          normed=True)[0]

    def build_axes(self, fig):
        """Create and return the list of axes in `fig` on which to plot."""

        return [fig.add_subplot(211), fig.add_subplot(212)]

    def analyze_inner(self, axs):
        """Do the analysis itself: compute lengths and plot the distributions.

        Parameters
        ----------
        axs : list of :class:`~matplotlib.axes.Axes` instances
            The axes on which to put plot.

        """

        print 'Analyzing paths'

        self.build_lengths()
        self.plot_observed(axs[0])
        self.plot_normalized_observed(axs[1])

    def print_fig_text(self, fig, title):
        """Print `title` on `fig` with some additional details on the
        analysis."""

        fig.text(0.5, 0.95,
                 self.latexize(title + ' --- '
                               + self.savefile_postfix()),
                 ha='center')

    def plot_observed(self, ax):
        """Plot the distribution of observed distances travelled on `ax`.

        See Also
        --------
        plot_normalized_observed

        """

        ax.plot(self.x, self.n_lengths, 'b',
                label='Observed ' + self.aa.ingraph_text)
        ax.set_xlabel('Distance')
        ax.set_ylabel('Probability density')
        ax.legend(loc='best')

    def plot_normalized_observed(self, ax):
        """Plot the distribution of observed distances travelled on `ax`,
        normalized to the distribution in the graph.

        Owing to the fact that there are many more words at distance `n+1` than
        there are at distance `n` from a given word, the distribution of
        travelled distances would be very naturally biased towards higher
        distances if the destination words were picked randomly. This means
        that looking at the raw distribution of distances travelled isn't very
        informative. Instead, this function plots the distribution of distances
        travelled, normalized to the distribution of distances in the
        underlying graph. This plot would be flat in the random case, and it
        tells us how often a distance appears *compared to random*.

        See Also
        --------
        plot_observed

        """

        c_distribution = self.distribution[self.x]
        ax.plot(self.x, self.n_lengths / c_distribution,
                'r', label='Normalized observed ' + self.aa.ingraph_text)
        ax.set_xlabel('Distance')
        ax.legend(loc='best')


class WNPathsAnalysis(BasePathsAnalysis):

    """WordNet paths analysis, based on BasePathsAnalysis.

    Visualize distances travelled in the WordNet graph upon substitution.

    Parameters
    ----------
    aa : :class:`AnalysisArgs` instance
        The analysis arguments used for the whole analysis.
    data : list
        The data on which to perform the paths analysis; usually a list of
        :class:`~mine.substitutions.Substitution`\ s.

    Attributes
    ----------
    filename : string
        Filename for the precomputed path lengths on the WordNet graph.
    load_graph : method
        Caching graph loader imported from :mod:`linguistics.wn`; makes
        sure the graph is only loaded once.

    See Also
    --------
    BasePathsAnalysis, FAPathsAnalysis, .base.AnalysisCase

    """

    def __init__(self, aa, data):
        """Initialize the structure from super.

        Parameters
        ----------
        aa : :class:`AnalysisArgs` instance
            The analysis arguments used for the whole analysis.
        data : list
            The data on which to perform the paths analysis; usually a list of
            :class:`~mine.substitutions.Substitution`\ s.

        """

        super(WNPathsAnalysis, self).__init__(aa, data)
        self.filename = st.wn_lengths_pickle
        self.load_graph = l_wn.build_wn_nxgraph

    def savefile_postfix(self):
        """Get the postfix to be added to the save file name."""

        return 'paths-wn'


class FAPathsAnalysis(BasePathsAnalysis):

    """Free Association paths analysis, based on BasePathsAnalysis.

    Visualize distances travelled in the Free Association graph upon
    substitution.

    Parameters
    ----------
    aa : :class:`AnalysisArgs` instance
        The analysis arguments used for the whole analysis.
    data : list
        The data on which to perform the paths analysis; usually a list of
        :class:`~mine.substitutions.Substitution`\ s.

    Attributes
    ----------
    filename : string
        Filename for the precomputed path lengths on the WordNet graph.
    load_graph : method
        Caching graph loader imported from :mod:`linguistics.wn`; makes
        sure the graph is only loaded once.

    See Also
    --------
    BasePathsAnalysis, WNPathsAnalysis, .base.AnalysisCase

    """

    def __init__(self, aa, data):
        """Initialize the structure from super.

        Parameters
        ----------
        aa : :class:`AnalysisArgs` instance
            The analysis arguments used for the whole analysis.
        data : list
            The data on which to perform the paths analysis; usually a list of
            :class:`~mine.substitutions.Substitution`\ s.

        """

        super(FAPathsAnalysis, self).__init__(aa, data)
        self.filename = st.fa_lengths_pickle
        self.load_graph = l_fa.build_fa_nxgraph

    def savefile_postfix(self):
        """Get the postfix to be added to the save file name."""

        return 'paths-fa'
