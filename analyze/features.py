#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze variations of feature values upon substitution."""


from __future__ import division

import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import networkx as nx

from util.generic import dict_plusone, indices_in_range, list_to_dict, inv_dict
from util.graph import caching_neighbors_walker
import datainterface.picklesaver as ps
from linguistics.treetagger import TaggerBuilder
import linguistics.wn as l_wn
from analyze.base import AnalysisCase
import settings as st


class Feature(object):

    """Load feature values, perform computations on them, and cache the
    results.

    Parameters
    ----------
    data_src : string
        The initial database source for the features (WordNet,
        Free Association).
    ftype : string
        The type of feature computed on the data source
        (degrees, PageRank, etc.).
    POS : string
        The POS category for the considered feature (a, n, v, r, all).

    Attributes
    ----------
    data_src : string
        The `data_src` passed to the constructor.
    ftype : string
        The `ftype` passed to the constructor.
    POS : string
        The `POS` passed to the constructor.
    fullname : string
        Full name of the feature, for logging and title building.
    filename : string
        Name of the file containing the computed feature values.
    lem : bool
        Whether or not words are to be lemmatized when using this feature.
    log : bool
        Whether or not to plot with a log-scale when showing graphs using this
        feature.
    _cache_fnw : dict
        Cache dict for :meth:`features_neighboring_word` values.
    _cache_fnr : dict
        Cache dict for :meth:`mean_feature_neighboring_range` values.

    See Also
    --------
    FeatureAnalysis, .substitutions.SubstitutionsAnalyzer

    """

    _cached_instances = {}

    def __init__(self, data_src, ftype, POS):
        """Initialize structure with feature information.

        Parameters
        ----------
        data_src : string
            The initial database source for the features (WordNet,
            Free Association).
        ftype : string
            The type of feature computed on the data source
            (degrees, PageRank, etc.).
        POS : string
            The POS category for the considered feature (a, n, v, r, all).

        """

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
        """Get feature value corresponding to `key`."""

        return self.data[key]

    @property
    def values(self):
        """Get all feature values, caching the loading of those values.

        See Also
        --------
        load

        """

        try:
            return self._values
        except:
            self.load()
            self._values = np.array(self.data.values())
            return self._values

    def load(self):
        """Load all feature values from file into memory.

        If `self.log` is ``True``, we will in fact be using the log values
        of the features. So all values are converted to log in the loading
        process. The result is stored in `self.data`. If the data was
        alreaydy previously loaded, nothing is done.

        """

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
        """Get the list of feature values for words around `word` at
        `distance` steps in the WordNet graph.

        This method is used when comparing features to the average local value
        around a given word: it finds all the neighbors of a word at a given
        distance in the WordNet graph, and lists the feature values of those
        words. Note that the WordNet graph is used as the graph to find
        neighbors, but it wasn't necessarily involved in creating the feature
        values we are dealing with. The feature we're working with could be
        Age-of-Acquisition, Mean Number of Phonemes, Free Association Degree,
        anything really.

        The results of these computations are cached each time a call to this
        method is made, so calling many times will eventually speed up.

        Parameters
        ----------
        word : string
            The word around which to look, which must already be lemmatized if
            needed.
        distance : int
            The distance to travel around `word` to collect neighbors.

        Returns
        -------
        list
            The feature values of the neighboring words.

        See Also
        --------
        mean_feature_neighboring_range

        """

        try:
            # Have we already cached a result?
            return self._cache_fnw[(word, distance)]

        except KeyError:
            # Make sure the feature values are loaded
            self.load()
            try:
                neighbors = self.walk_neighbors(word, distance)
            except nx.NetworkXError:
                # If the word was not found, return None
                f = None
            else:
                # Remove the origin word
                neighbors.discard(word)

                # Get the collected words' feature values
                f = []
                for w in neighbors:
                    try:
                        f.append(self.data[w])
                    except KeyError:
                        # Don't fail if a word doesn't exist in the
                        # feature values
                        continue

                # If none of the collected words had feature values,
                # return None
                if len(f) == 0:
                    f = None
                else:
                    f = np.array(f)

            # Cache our results
            self._cache_fnw[(word, distance)] = f
            return f

    def mean_feature_neighboring_range(self, f_range, distance):
        """Compute the average feature value for words neighboring words with
        features in a given range.

        This method finds all the words having feature values in `f_range`,
        finds all their neighbors at `distance` steps in the WordNet graph,
        and averages the feature values of all those neighboring words. This
        results in the average feature value for words neighboring words
        having themselves feature values in `f_range`. Kind of the average
        neighbor value around `f_range`. Note that the WordNet graph is used
        to find neighbors, but isn't necessarily involved in how the feature
        we're considering was computed (that feature could be
        Age-of-Acquisition, Free Association Degrees, anything really).

        The results of these computations are cached each time a call to this
        method is made, so calling many times will eventually speed up.

        Parameters
        ----------
        f_range : tuple or list
            Feature range around which to explore the average feature value.
        distance : int
            Distance to travel in the WordNet graph to find neighbors.

        Returns
        -------
        float
            Resulting average feature value.

        See Also
        --------
        features_neighboring_word, FeatureAnalysis.build_h0

        """

        try:
            # Have we already cached a result?
            return self._cache_fnr[(f_range, distance)]

        except KeyError:
            # Make sure the feature values are loaded
            self.load()

            # Find the words with feature values in our range
            # (this is a convoluted way of doing a `filter` on a dict,
            # as I discovered later. But it could be more efficient on large
            # arrays.)
            idx = indices_in_range(self.values, f_range)
            all_words = self.data.keys()
            words = [all_words[i] for i in idx]

            # Get average feature value around each word
            features = []
            for w in words:
                features_w = self.features_neighboring_word(w, distance)
                if features_w is not None:
                    features.append(features_w.mean())

            # Return None if no words were found, or the average of averages
            if len(features) == 0:
                f = None
            else:
                f = np.array(features).mean()

            # And cache our results
            self._cache_fnr[(f_range, distance)] = f
            return f

    @classmethod
    def iter_features(cls, aa):
        """Iterate over all features specified in `aa`, yielding a
        :class:`Feature` instance for each.

        Parameters
        ----------
        aa : :class:`~analyze.args.AnalysisArgs` instance
            The `AnalysisArgs` specifying the features to iterate over.

        See Also
        --------
        .substitutions.SubstitutionsAnalyzer

        """

        for s, ts in aa.features.iteritems():
            for t in ts:
                yield cls.get_instance(s, t, aa.POS)

    @classmethod
    def load_G(cls):
        """Load WordNet graph and create a caching neighbor-walking method.

        The results are stored in `cls.G` (graph) and `cls.walk_neighbors`
        (neighbor-walking method). If all this was already loaded, nothing
        is done.

        """

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
        """Create an instance of :class:`Feature`.

        Or return a cached instance if another one was already created for
        these parameters.

        Parameters
        ----------
        data_src : string
            The initial database source for the features (WordNet,
            Free Association).
        ftype : string
            The type of feature computed on the data source
            (degrees, PageRank, etc.).
        POS : string
            The POS category for the considered feature (a, n, v, r, all).

        Returns
        -------
        feature
            The created :class:`Feature` instance.

        """

        cls.load_G()
        try:
            return cls._cached_instances[(data_src, ftype, POS)]
        except KeyError:
            f = Feature(data_src, ftype, POS)
            cls._cached_instances[(data_src, ftype, POS)] = f
            return f


class FeatureAnalysis(AnalysisCase):

    """Analyze the evolution of a feature upon substitution.

    This class holds all the necessary methods to plot the variations of a
    feature upon substitutions and the susceptibility of a feature to be
    substituted, for a given set of analysis arguments. It also hold the
    methods to compute the :math:`H_0` and :math:`H_{0,n}`
    (or :math:`H_{00}` in the paper) null hypotheses.

    Parameters
    ----------
    aa : :class:`AnalysisArgs` instance
        The set of arguments to analyze for.
    data : list
        List of :class:`~mine.substitutions.Substitution`\ s to analyze.
    feature : :class:`Feature` instance
        The feature to analyze for.

    Attributes
    ----------
    tagger : :class:`~linguistics.treetagger.TreeTaggerTags` instance
        Caching tagger to use during the analysis.
    feature : :class:`Feature` instance
        The `Feature` instance given to the constructor.
    log_text : string
        Text included in figure titles if we are using log values.
    nbins : int
        Number of bins for the feature values, used in all plots.
    bins : np.ndarray
        The actual bins.
    bin_middles : np.ndarray
        Array of the middle of the bins.
    w1 : string
        Either `lem1` if words are to be lemmatized, or `word1` otherwise.
        Used to retrieve the right value from
        :class:`~mine.substitutions.Substitution` instances.
    w2 : string
        Either `lem2` if words are to be lemmatized, or `word2` otherwise.
        Used to retrieve the right value from
        :class:`~mine.substitutions.Substitution` instances.

    See Also
    --------
    .base.AnalysisCase, .substitutions.SubstitutionsAnalyzer

    """

    def __init__(self, aa, data, feature):
        """Initialize the structure with arguments, data, and a feature.

        Parameters
        ----------
        aa : :class:`AnalysisArgs` instance
            The set of arguments to analyze for.
        data : list
            List of :class:`~mine.substitutions.Substitution`\ s to analyze.
        feature : :class:`Feature` instance
            The feature to analyze for.

        """

        self.tagger = TaggerBuilder.get_tagger()

        # We need the feature to be calling savefile_postfix in super
        self.feature = feature
        super(FeatureAnalysis, self).__init__(aa, data)
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

    def build_axes(self, fig):
        """Return a list of :class:`~matplotlib.axes.Axes` instances in `fig`
        to plot on."""

        return [fig.add_subplot(111)]

    def analyze_inner(self, axs):
        """Run the analysis in itself, plotting on the axes in `axs`."""

        print 'Analyzing feature ' + self.feature.fullname

        self.feature.load()

        #self.plot_variations_from_h0_n(axs[0])
        #self.plot_mothers_distribution(axs[0])

        #self.plot_daughters_distribution(axs[0])
        #self.plot_variations_from_h0(axs[0])
        #self.plot_variations(axs[0])

        #ax = self.fig.add_subplot(224)
        #ax = self.fig.add_subplot(111)
        self.plot_susceptibilities(axs[0])
        #self.plot_variations_from_h0_h0_n(axs[0])
        #self.plot_variations_from_h0(axs[0])
        #self.plot_variations(axs[0])

    def print_fig_text(self, fig, title):
        """Print `title` and this analysis' feature name on `fig`."""

        fig.text(0.5, 0.95,
                 self.latexize(title +
                               ' --- ' + self.feature.fullname),
                 ha='center')

    def savefile_postfix(self):
        """Return the postfix for the file to which the figure
        could be saved."""

        return self.feature.fullname

    def _plot_distribution(self, ax, values):
        """Plot the distriution of `values` on `ax`.

        The distribution is estimated with a gaussian kernel, and plotted above
        the histogram of `values`.

        """

        ax.hist(values, bins=self.bins, normed=True,
                log=self.feature.log)
        kde = gaussian_kde(values)
        x = np.linspace(self.bins[0], self.bins[-1], 100)
        ax.plot(x, kde(x), 'g')

    def plot_mothers_distribution(self, ax):
        """Plot the distribution of mother features on `ax`."""

        self.build_l2_f_lists()

        self._plot_distribution(ax, self.l2_f_mothers)

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('\\# mothers' + self.log_text)

    def plot_daughters_distribution(self, ax):
        """Plot the distribution of daughter features on `ax`."""

        self.build_l2_f_lists()

        self._plot_distribution(ax, self.l2_f_daughters)

        ax.set_xlabel('Daughter feature')
        ax.set_ylabel('\\# daughters' + self.log_text)

    def plot_susceptibilities(self, ax):
        """Build the susceptibility plot for our feature on `ax`.

        This build a colored histogram representing the susceptibility of each
        feature value to attract a substitution (the colors represent the
        susceptibility, the histogram is that of the feature values
        distribution).

        See the paper for the formal definition of what susceptibility means
        here.

        See Also
        --------
        build_susceptibilities

        """

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
        ax.figure.colorbar(sm, ax=ax)

        ax.set_xlabel('Pool feature')
        ax.set_ylabel('Susceptibilities in color' + self.log_text)

    def plot_variations(self, ax):
        """Plot the absolute feature variations upon subtitution, on `ax`."""

        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')
        #ax.plot(self.bin_middles, self.v_d_h0, 'r',
                #label='$H_0$ ' + self.aa.ingraph_text)
        #ax.plot(self.bin_middles, self.v_d_h0_n, 'c',
                #label='$H_{0,n}$ ' + self.aa.ingraph_text)

        ax.plot(self.bin_middles, self.v_d,
                #'b',
                linewidth=2,
                label='$<f(daughter) - f(mother)>$ ' + self.aa.ingraph_text)
        #ax.plot(self.bin_middles, self.v_d - self.v_d_std, 'm',
                #label='IC-95\\% ' + self.aa.ingraph_text)
        #ax.plot(self.bin_middles, self.v_d + self.v_d_std, 'm')

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from mother' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def plot_variations_from_h0_h0_n(self, ax):
        """Plot the deviation of feature variation compared to H0 and H0n,
        on `ax`."""

        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')

        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0,
                'b', linewidth=2,
                label='$\\Delta - \\Delta_{H_0}$ ' + self.aa.ingraph_text)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0 - self.daughter_d_std,
                'b', linewidth=0.5, alpha=0.5,
                label='IC-95\\% ' + self.aa.ingraph_text)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0 + self.daughter_d_std,
                'b', linewidth=0.5, alpha=0.5)

        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n,
                'c', linewidth=2,
                label='$\\Delta - \\Delta_{H_{0,n}}$ ' + self.aa.ingraph_text)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n - self.daughter_d_std,
                'c', linewidth=0.5, alpha=0.5,
                label='IC-95\\% ' + self.aa.ingraph_text)
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n + self.daughter_d_std,
                'c', linewidth=0.5, alpha=0.5)

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from $H_0$ / $H_{0,n}$' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def plot_variations_from_h0(self, ax, chrome=True, color=None):
        """Plot the deviation of feature variation compared to H0, on `ax`.

        Parameters
        ----------
        chrome : bool
            Whether or not to add legend, title, and fix the x limits. Used for
            stacking plots on one another.
        color : matplotlib color
            Color to be used for the main deviation curve. Used for stacking
            plots on one another.

        """

        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins))  # , 'k')
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0,
                #color=color or 'b',
                linewidth=2 if self.aa.POS == 'all' else 1,
                label='$\\Delta - \\Delta_{H_0}$ ' + self.aa.ingraph_text)

        if chrome:
            #ax.plot(self.bin_middles,
                    #self.daughter_d - self.daughter_d_h0 - \
                        #self.daughter_d_std,
                    #'m', label='IC-95\\% ' + self.aa.ingraph_text)
            #ax.plot(self.bin_middles,
                    #self.daughter_d - self.daughter_d_h0 + \
                        #self.daughter_d_std,
                    #'m')

            ax.set_xlabel('Mother feature')
            ax.set_ylabel('Variations from $H_0$' + self.log_text)
            ax.set_xlim(self.bins[0], self.bins[-1])
            ax.legend(loc='best', prop={'size': 8})

    def plot_variations_from_h0_n(self, ax):
        """Plot the deviation of feature variation compared to H0n, on `ax`."""

        self.build_h0()
        self.build_variations()

        ax.plot(self.bin_middles, np.zeros(self.nbins), 'k')
        ax.plot(self.bin_middles,
                self.daughter_d - self.daughter_d_h0_n,
                #'b',
                linewidth=2 if self.aa.POS == 'all' else 1,
                label='$\\Delta - \\Delta_{H_{0,n}}$ ' + self.aa.ingraph_text)
        #ax.plot(self.bin_middles,
                #self.daughter_d - self.daughter_d_h0_n - self.daughter_d_std,
                #'m', label='IC-95\\% ' + self.aa.ingraph_text)
        #ax.plot(self.bin_middles,
                #self.daughter_d - self.daughter_d_h0_n + self.daughter_d_std,
                #'m')

        ax.set_xlabel('Mother feature')
        ax.set_ylabel('Variations from $H_{0,n}$' + self.log_text)
        ax.set_xlim(self.bins[0], self.bins[-1])
        ax.legend(loc='best', prop={'size': 8})

    def build_h0(self):
        """Build values for the :math:`H_0` and :math:`H_{0,n}` hypotheses
        for each bin.

        :math:`H_0` supposes that words are chosen randomly in the pool of
        words that have a value assigned for the considered feature.
        :math:`H_{0,n}` supposes that words are chosen randomly in that same
        pool restricted to synonyms of the mother word (neighbors at distance 1
        on the WordNet graph). See the paper for more details.

        This method builds the hypothesized daughter values and ``daughter -
        mother`` variations for each bin.

        The daughter values for :math:`H_0` and :math:`H_{0,n}` are stored in
        `self.daughter_d_h0` and `self.daughter_d_h0_n` respectively. The
        ``daughter - mother`` variations are stored in `self.v_d_h0` and
        `self.v_d_h0_n` respectively.

        If those values have already been computed, nothing is done.

        """

        try:
            # Did we already compute these? If so, do nothing.
            self.daughter_d_h0
            self.daughter_d_h0_n
            self.v_d_h0
            self.v_d_h0_n

        except AttributeError:
            # Create the arrays
            self.daughter_d_h0 = np.zeros(self.nbins)
            self.daughter_d_h0_n = np.zeros(self.nbins)
            self.v_d_h0 = np.zeros(self.nbins)
            self.v_d_h0_n = np.zeros(self.nbins)

            for i in range(self.nbins):
                bin_ = (float(self.bins[i]), float(self.bins[i + 1]))

                # Compute the average neighbor feature for this bin
                neighbors_feature = \
                    self.feature.mean_feature_neighboring_range(bin_, 1)
                idx = indices_in_range(self.feature.values, bin_)

                # Store if anything was found, skip otherwise
                if len(idx) > 0:
                    if neighbors_feature is not None:
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
        """Build the variation and std of feature values upon substitution,
        for each bin.

        Four arrays are built: the daughter words feature values, the std of
        that, the ``daughter - mother`` feature variations, and the std of
        that, all stored respectively in `self.daughter_d`,
        `self.daughter_d_std`, `self.v_d`, and `self.v_d_std`.

        The feature values used are in fact averages over several
        substitutions: substitutions occurring in the same cluster and on the
        same start word are likely not independent, so we average arrival
        feature values over same-cluster-same-start-word substitutions before
        anything else. That way, confidence intervals are really computed on
        statistically independent occurrences. These values are called
        "level-2" values (as opposed to the raw values called "level-1"), and
        are computed in :meth:`build_l2_f_lists`.

        If the arrays have already been computed previously, nothing is done.

        See Also
        --------
        build_l2_f_lists

        """

        try:
            # Have we already computed these? If so, do nothing.
            self.daughter_d
            self.daughter_d_std
            self.v_d
            self.v_d_std

        except AttributeError:
            # Make sure l2 values have been computed
            self.build_l2_f_lists()

            # The target arrays to be filled
            self.daughter_d = np.zeros(self.nbins)
            self.daughter_d_std = np.zeros(self.nbins)
            self.v_d = np.zeros(self.nbins)
            self.v_d_std = np.zeros(self.nbins)

            for i in range(self.nbins):
                bin_ = (self.bins[i], self.bins[i + 1])

                idx = indices_in_range(self.l2_f_mothers, bin_)

                # Compute the values if anything was found in that range,
                # otherwise skip silently.
                # We need > 1 here to make sure the std computing works.
                if len(idx) > 1:

                    daughter_dd = self.l2_f_daughters[idx]
                    self.daughter_d[i] = daughter_dd.mean()
                    self.daughter_d_std[i] = (1.96 * daughter_dd.std() /
                                              np.sqrt(len(idx) - 1))

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
        """Compute susceptibility values for each bin.

        Susceptibility is built as the number of times a word is substituted
        divided by the number of times that word appears in a quote where a
        substitution occurs, whether it occurs on that word or not (the fact
        that a substitution occurs on that quote means that the word was in a
        "substitutable" position).

        The values are then aggregated to compute the average susceptibility
        for each bin. This array is stored in `self.f_susceptibilities`. If the
        array was already computed previously, nothing is done.

        See Also
        --------
        plot_susceptibilities

        """

        try:
            # Did we already compute this before? If so, do nothing.
            self.f_susceptibilities

        except AttributeError:

            possibilities = {}
            realizations = {}

            for s in self.data:

                # Lemmatize if asked to
                if self.feature.lem:
                    # This will take advantage of data from
                    # future analyses where the lemmas are directly
                    # included in the data. If they're not, do the
                    # lemmatizing on-the-fly.
                    try:
                        words = s.mother.lems
                    except AttributeError:
                        words = self.tagger.Lemmatize(s.mother)
                else:
                    words = s.mother.tokens

                # Update possibilities
                for w in words:
                    dict_plusone(possibilities, w)

                # And realizations
                dict_plusone(realizations, s[self.w1])

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

                # Only store the words which exist in our feature list
                try:
                    self.f_susceptibilities.append([self.feature(w), ws])
                except KeyError:
                    pass

            # Sort by feature value for future use
            self.f_susceptibilities = np.array(self.f_susceptibilities)
            o = np.argsort(self.f_susceptibilities[:, 0])
            self.f_susceptibilities = self.f_susceptibilities[o]

    def build_l2_f_cl_m_ids(self):
        """Build the dict of indices for level-2 averaging.

        Since substitutions occurring in the same cluster and with the same
        start words are not independent, we regularly average feature values
        over same-cluster-same-start-word occurrences. Those average values are
        called "level-2" values, and the original ones are called "level-1"
        values.

        Level-1 values are computed in :meth:`build_f_lists`, and have all the
        same size (it is the length of `self.data` minus the substitutions
        where the start or end word doesn't figure in our feature pool).

        This method builds the dict of `(cluster id, start word)` to `indices
        in data` mapping, which is then used by :meth:`l2_values` to compute
        the level-2 values for any given level-1 array of values. If the dict
        was already computed previously, nothing is done.

        See Also
        --------
        l2_values, build_f_lists, build_l2_f_lists

        """

        try:
            self.l2_f_cl_m_ids
        except AttributeError:
            self.l2_f_cl_m_ids = list_to_dict(self.f_cl_m_ids)

    def l2_values(self, l1_values):
        """Compute the level-2 values corresponding to `l1_values`.

        See :meth:`build_l2_f_cl_m_ids` for an explanation on level-1 and
        level-2 values.

        See Also
        --------
        build_l2_f_cl_m_ids

        """

        l2_values = []

        for idx in self.l2_f_cl_m_ids.itervalues():
            l2_values.append(l1_values[idx].mean())

        return np.array(l2_values)

    def build_w_lists(self):
        """Build the lists of mother and daughter words, as well as the
        corresponding cluster ids.

        The lists are stored respectively in `self.mothers`, `self.daughters`,
        and `self.cl_ids`. If they were already computed earlier, nothing is
        done.

        These lists are used later in :meth:`build_f_lists`.

        See Also
        --------
        build_f_lists

        """

        try:
            # Have we already computed these before? If so, do nothing.
            self.mothers
            self.daughters
            self.cl_ids

        except AttributeError:
            # Extract lists from the data
            self.mothers = [s[self.w1] for s in self.data]
            self.daughters = [s[self.w2] for s in self.data]
            self.cl_ids = [s.mother.cl_id for s in self.data]

    def build_f_lists(self):
        """Build the lists of feature values for mothers, daughters, and the
        corresponding list of `(cluster id, mother)` tuples.

        The lists are stored respectively in `self.f_mothers`,
        `self.f_daughters`, and `self.f_cl_m_ids`. If they were already
        computed earlier, nothing is done.

        These lists and then used in :meth:`build_l2_f_lists` to compute the
        corresponding level-2 values (see :meth:`build_l2_f_cl_m_ids` for an
        explanation on level-1 and level-2 values). The list of `(cluster id,
        mother)` tuples is especially used in :meth:`build_l2_f_cl_m_ids`,
        necessary step to compute all further level-2 values.

        See Also
        --------
        build_w_lists, build_l2_f_lists, build_l2_f_cl_m_ids

        """

        try:
            # Have we already computed these before? If so, do nothing.
            self.f_mothers
            self.f_daughters
            self.f_cl_m_ids

        except AttributeError:
            # First build the word lists, we use them here
            self.build_w_lists()
            self.f_mothers = []
            self.f_daughters = []
            self.f_cl_m_ids = []

            for m, d, cl_id in zip(self.mothers, self.daughters, self.cl_ids):

                # If either mother or daughter is not found in the
                # feature pool, skip silently
                try:
                    f_m = self.feature(m)
                    f_d = self.feature(d)
                except KeyError:
                    continue

                self.f_mothers.append(f_m)
                self.f_daughters.append(f_d)
                self.f_cl_m_ids.append((cl_id, m))

            self.f_mothers = np.array(self.f_mothers)
            self.f_daughters = np.array(self.f_daughters)

    def build_l2_f_lists(self):
        """Build level-2 feature values for mothers and daughters.

        The feature values are stored respectively in `self.l2_f_mothers` and
        `self.l2_f_daughters`. If they were already computed earlier, nothing
        is done.

        The level-2 values are computed in :meth:`l2_values` (see
        :meth:`build_l2_f_cl_m_ids` for an explanation on level-1 and level-2
        values).

        See Also
        --------
        l2_values, build_f_lists, build_l2_f_cl_m_ids

        """

        try:
            # Have we already computed these before? If so, do nothing.
            self.l2_f_mothers
            self.l2_f_daughters

        except AttributeError:
            # First build level-1 feature lists and level-2 indices,
            # we need them later on.
            self.build_f_lists()
            self.build_l2_f_cl_m_ids()

            self.l2_f_mothers = self.l2_values(self.f_mothers)
            self.l2_f_daughters = self.l2_values(self.f_daughters)
