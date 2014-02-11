#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Argument classes for analysis of substitutions.

These classes are used to define arguments in the analysis scripts
(:mod:`analyze_substitutions` and :mod:`analyze_substitutions_multiple`).

"""


from __future__ import division

import re

import numpy as np

from baseargs import BaseArgs, MultipleBaseArgs
import settings as st


class AnalysisArgs(BaseArgs):

    """Arguments for analysis of one list of substitutions.

    It defines all necessary arguments for an analysis of mined substitutions,
    and is pluggable into most structures that are related to such an
    analysis. It is also the main object that :class:`MultipleAnalysisArgs`
    manipulates. This class inherits from :class:`~baseargs.BaseArgs`.

    Parameters
    ----------
    init_dict : dict, optional
        Dictionary of arguments to fill the instance with. If not provided,
        the arguments will be taken from the command line. Defaults to
        ``None``.

    Attributes
    ----------
    features : dict
        Subportion of the dict of features defined by :mod:`settings`. \
                Specifies which features to analyze for.
    positions : bool
        Whether or not to analyze positions of substituted words.
    paths : bool
        Whether or not to analyze distances travelled upon substitution.
    save : bool
        Whether or not to save the generated plots to files.
    overwrite : bool
        Whether or not to overwrite existing files when saving plots.
    show : bool
        Whether or not to show the plots generated (vs. only saving them).
        (`!show` implies `save`.)

    See Also
    --------
    baseargs.BaseArgs, MultipleAnalysisArgs

    """

    description = 'analyze substitutions (haming_word-distance == 1)'

    def __init__(self, init_dict=None):
        """Initialize the structure from command line or provided parameters.

        Parameters
        ----------
        init_dict : dict, optional
            Dictionary of arguments to fill the instance with. If not provided,
            the arguments will be taken from the command line. Defaults to
            ``None``.

        """

        super(AnalysisArgs, self).__init__(init_dict)

        if init_dict is None:

            self.parse_features(self.args.features)
            self.positions = self.args.positions
            self.paths = self.args.paths
            self.save = self.args.save
            self.overwrite = self.args.overwrite
            self.show = self.args.show

        else:

            self.parse_features(init_dict['features'])
            self.positions = init_dict['positions']
            self.paths = init_dict['paths']
            self.save = init_dict['save']
            self.overwrite = init_dict['overwrite']
            self.show = init_dict['show']

        # No show implies save
        self.save = self.save or (not self.show)

    def parse_features(self, f_strings):
        """Parse the ``--features`` argument from the command line.

        The result, a subportion of the dict of features defined by
        :mod:`settings`, is stored in `self.features`.

        Parameters
        ----------
        f_strings : list of strings
            The ``--features`` argument extracted from the command line.

        """

        self.features = {}

        if f_strings is None:
            for s in st.mt_analysis_features.iterkeys():
                self.features[s] = set(st.mt_analysis_features[s].keys())
            return

        if f_strings[0] == 'None':
            return

        for f_string in f_strings:
            parts = re.split('_', f_string)
            if not parts[0] in self.features:
                self.features[parts[0]] = set([])
            if len(parts) > 1:
                self.features[parts[0]].add('_'.join(parts[1:]))

        for s in self.features.iterkeys():
            if len(self.features[s]) == 0:
                self.features[s] = set(st.mt_analysis_features[s].keys())

    def create_argparser(self):
        """Create the argument parser to extract arguments from command line.

        This method is used by :class:`~baseargs.BaseArgs`'s constructor.

        Returns
        -------
        p : :class:`~argparse.ArgumentParser`
            The argument parser used to parse the command line arguments.

        """

        # Create the arguments parser.

        p = super(AnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t
                     for s in st.mt_analysis_features.iterkeys()
                     for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)
        p.add_argument('--no-positions', dest='positions',
                       action='store_const', const=False, default=True,
                       help="don't analyze positions of substitutions")
        p.add_argument('--no-paths', dest='paths', action='store_const',
                       const=False, default=True,
                       help="don't analyze path lengths of substitutions")
        p.add_argument('--save', dest='save', action='store_const',
                       const=True, default=False,
                       help='save figures to files')
        p.add_argument('--overwrite', dest='overwrite', action='store_const',
                       const=True, default=False,
                       help='overwrite existing figure files')
        p.add_argument('--no-show', dest='show', action='store_const',
                       const=False, default=True,
                       help=("don't show the graphs, just save the file. "
                             'This implies --save'))

        return p

    def print_analysis(self):
        """Print details of the analysis specified by the instance."""

        print
        print 'Analyzing with the following args:'
        print '  ff = {}'.format(self.ff)
        print '  model = {}'.format(self.model)
        print '  substrings = {}'.format(self.substrings)
        print '  POS = {}'.format(self.POS)
        if self.is_fixedslicing_model():
            print '  n_timebags = {}'.format(self.n_timebags)
        if len(self.features) != 0:
            print '  features = {}'.format(self.features)
        print '  positions = {}'.format(self.positions)
        print '  paths = {}'.format(self.paths)
        print '  save = {}'.format(self.save)
        print '  overwrite = {}'.format(self.overwrite)
        print '  show = {}'.format(self.show)


class GroupAnalysisArgs(object):

    """Group of :class:`AnalysisArgs` to be used in a same figure.

    This class is how `AnalysisArgs`\ s get grouped when plotting several
    distinct `AnalysisArgs` on the same figure. When using the ``--ingraph``
    option, the plots for different `AnalysisArgs` get grouped into single
    figures. This class represents a group of such `AnalysisArgs` that is
    yielded when iterating over an instance of :class:`MultipleAnalysisArgs`.

    Parameters
    ----------
    aas : list
        List of :class:`AnalysisArgs` that are to be grouped in the same
        figure.
    maa : :class:`MultipleAnalysisArgs` instance
        The parent `MultipleAnalysisArgs` that is generating this
        `GroupAnalysisArgs`.
    s : tuple
        The tuple of indices used to extract the `aas` list of
        `AnalysisArgs` from the parent `MultipleAnalysisArgs`. This is
        used to construct a title for the figure.

    Attributes
    ----------
    aas : list
        The `aas` parameter given to the constructor.
    save : bool
        Whether or not to save the generated plots to files. Extracted from
        the parent `MultipleAnalysisArgs`.
    ffs_text : string
        String indicating the framings and filterings included in the group.
        Used for the figure's title.
    models_text : string
        String indicating the models included in the group.
        Used for the figure's title.
    substringss_text : string
        String indicating the substrings-handling behaviours included in the
        group. Used for the figure's title.
    POSs_text : string
        String indicating the POSs included in the group. Used for the
        figure's title.
    has_fixedslicing_model : bool
        Whether or not the group of `AnalysisArgs` includes a fixed slicing
        model. Used for the figure's title.

    See Also
    --------
    AnalysisArgs, MultipleAnalysisArgs

    """

    def __init__(self, aas, maa, s):
        """Initialize structure from a list of :class:`AnalysisArgs`, a
        :class:`MultipleAnalysisArgs`, and the slicing of the latter.

        Parameters
        ----------
        aas : list
            List of :class:`AnalysisArgs` that are to be grouped in the same
            figure.
        maa : :class:`MultipleAnalysisArgs` instance
            The parent `MultipleAnalysisArgs` that is generating this
            `GroupAnalysisArgs`.
        s : tuple
            The tuple of indices used to extract the `aas` list of
            `AnalysisArgs` from the parent `MultipleAnalysisArgs`. This is
            used to construct a title for the figure.

        """

        self.aas = aas
        self.save = maa.save

        # Build texts for filenames
        self.ffs_text = ','.join(maa.ffs) \
            if s[0] is Ellipsis else maa.ffs[s[0]]
        self.models_text = ','.join(maa.models) \
            if s[1] is Ellipsis else maa.models[s[1]]
        if s[2] is Ellipsis:
            self.substringss_text = ','.join(['yes' if ss else 'no'
                                              for ss in maa.substringss])
        else:
            self.substringss_text = 'yes' if maa.substringss[s[2]] else 'no'
        self.POSs_text = ','.join(maa.POSs) \
            if s[3] is Ellipsis else maa.POSs[s[3]]

        # If we have a fixed slicing model in the lot, remember it
        # for later when we create the title
        fixedslicing_models = [aa.is_fixedslicing_model() for aa in aas]
        if sum(fixedslicing_models):
            self.has_fixedslicing_model = True
            self.n_timebags_text = \
                aas[fixedslicing_models.index(True)].n_timebags
        else:
            self.has_fixedslicing_model = False

        # Build text for in graph legend
        for aa in aas:
            text_to_include = []
            if s[0] is Ellipsis:
                text_to_include.append('ff: ' + aa.ff)
            if s[1] is Ellipsis:
                text_to_include.append('model: ' + aa.model)
            if s[2] is Ellipsis:
                text_to_include.append('sub: ' + aa.substrings)
            if s[3] is Ellipsis:
                text_to_include.append('POS: ' + aa.POS)
            aa.ingraph_text = ' | '.join(text_to_include)

    def __iter__(self):
        """Iterate over all included :class:`AnalysisArgs`."""

        for aa in self.aas:
            yield aa

    def title(self):
        """Build a title representing the type of analysis specified.

        Returns
        -------
        title : string
            The built title.

        """

        title = 'ff: {} | model: {} | sub: {} | POS: {}'.format(
            self.ffs_text, self.models_text, self.substringss_text,
            self.POSs_text)
        if self.has_fixedslicing_model:
            title += ' | n: {}'.format(self.n_timebags_text)
        return title


class MultipleAnalysisArgs(MultipleBaseArgs):

    """Arguments for analysis of multiple lists of substitutions.

    It defines all necessary arguments for analysis of substitutions mined
    with several sets of arguments, and is usable with the
    :class:`~.substitutions.SubstitutionsAnalyzer`. This class inherits from
    :class:`~baseargs.MultipleBaseArgs`.

    Attributes
    ----------
    features : dict
        Subportion of the dictionary of features defined in :mod:`settings`, \
        specifying which features to analyze for.
    ingraph : list of strings
        List of strings specifying which analysis dimensions to include in
        single graphs.
    positions : bool
        Whether or not to analyze positions of substituted words.
    paths : bool
        Whether or not to analyze distances travelled upon substitution.
    save : bool
        Whether or not to save the generated plots to files.
    overwrite : bool
        Whether or not to overwrite existing files when saving plots.
    show : bool
        Whether or not to show the plots generated (v. only saving them)
        (`!show` implies `save`).

    See Also
    --------
    baseargs.MultipleBaseArgs, AnalysisArgs

    """

    description = 'analyze substitutions for various argument sets'

    def __init__(self):
        """Initialize the instance with arguments from the command line."""

        super(MultipleAnalysisArgs, self).__init__()

        self.features = self.args.features
        self.ingraph = self.args.ingraph or []
        self.positions = self.args.positions
        self.paths = self.args.paths
        self.save = self.args.save
        self.overwrite = self.args.overwrite
        self.show = self.args.show

        # No show implies save
        self.save = self.save or (not self.show)

        # Create the AnalysisArgs array
        self.ingraph_c = {'ff', 'model',
                          'substrings', 'POS'}.difference(self.ingraph)
        self.build_aas_ndarray()

    def __iter__(self):
        """Iterate over all :class:`GroupAnalysisArgs`, slicing the parameter
        space as we go."""

        # Create the list of slicing tuples
        slices = set()
        for ff_idx in range(len(self.ffs)):
            for model_idx in range(len(self.models)):
                for substrings_idx in range(len(self.substringss)):
                    for POS_idx in range(len(self.POSs)):
                        s = ()
                        s += (ff_idx if 'ff' in self.ingraph_c else Ellipsis,)
                        s += (model_idx
                              if 'model' in self.ingraph_c else Ellipsis,)
                        s += (substrings_idx
                              if 'substrings' in self.ingraph_c else Ellipsis,)
                        s += (POS_idx
                              if 'POS' in self.ingraph_c else Ellipsis,)
                        slices.add(s)

        for s in slices:
            y = self.aas_ndarray[s]
            if isinstance(y, np.ndarray):
                yield GroupAnalysisArgs(y.flatten(), self, s)
            else:
                yield GroupAnalysisArgs([y], self, s)

    def build_aas_ndarray(self):
        """Build a 4-dimensional array of the :class:`AnalysisArgs` included
        in this `MultipleAnalysisArgs`.

        This structure lets the `__iter__` method create any kinds of slices
        through the parameter space, to allow arbitrary grouping of parameters
        in single figures as per the ``--ingraph`` command line option.

        The result is stored in `self.aas_ndarray`.

        """

        self.aas_shape = (len(self.ffs), len(self.models),
                          len(self.substringss), len(self.POSs))
        self.aas_ndarray = np.ndarray(self.aas_shape, dtype=AnalysisArgs)

        for i, ff in enumerate(self.args.ffs):

            for j, model in enumerate(self.args.models):

                for k, substrings in enumerate(self.args.substringss):

                    for l, POS in enumerate(self.args.POSs):

                        init_dict = self.create_init_dict(ff,
                                                          model,
                                                          substrings,
                                                          POS)

                        if model in st.mt_mining_fixedslicing_models:

                            if len(self.args.n_timebagss) > 1:
                                raise ValueError("can't have multiple "
                                                 "n_timebags values when "
                                                 "using --ingraph option")

                            init_dict['n_timebags'] = int(self.n_timebagss[0])
                            self.aas_ndarray[i, j, k, l] = \
                                self.create_args_instance(init_dict)

                        else:

                            self.aas_ndarray[i, j, k, l] = \
                                self.create_args_instance(init_dict)

    def create_init_dict(self, ff, model, substrings, POS):
        """Create an initialization dict.

        This will produce an initialization dict suitable for creation of
        an instance of :class:`AnalysisArgs`, merging the parameters provided
        and the arguments stored in attributes of `self`.

        This method is used by :class:`~baseargs.MultipleBaseArgs`'s
        constructor.

        Parameters
        ----------
        ff : string
            The type of filtering for the clusters.
        model : string
            The substitution detection model.
        substrings : bool
            Whether or not to include substitutions from substrings of quotes.
        POS : string
            The type of POS filtering.

        Returns
        -------
        init_dict : dict
            The initialization dict resulting of parameters merged with
            internal attributes.

        """

        init_dict = super(MultipleAnalysisArgs,
                          self).create_init_dict(ff, model,
                                                 substrings, POS)
        init_dict['features'] = self.args.features
        init_dict['positions'] = self.args.positions
        init_dict['paths'] = self.args.paths
        init_dict['save'] = self.args.save
        init_dict['overwrite'] = self.args.overwrite
        init_dict['show'] = self.args.show
        return init_dict

    def create_args_instance(self, init_dict):
        """Create an :class:`AnalysisArgs` instance.

        This method is used by :class:`~baseargs.MultipleBaseArgs`'s
        constructor.

        Parameters
        ----------
        init_dict : dict
            The initialization dictionary for the :class:`AnalysisArgs`.

        Returns
        -------
        aa : :class:`AnalysisArgs`
            The initialized instance.

        """

        return AnalysisArgs(init_dict)

    def create_argparser(self):
        """Create the argument parser to extract arguments from command line.

        This method is used by :class:`~baseargs.MultipleBaseArgs`'s
        constructor.

        Returns
        -------
        p : :class:`~argparse.ArgumentParser`
            The argument parser used to parse the command line arguments.

        """

        # Create the arguments parser.

        p = super(MultipleAnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t
                     for s in st.mt_analysis_features.iterkeys()
                     for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)
        p.add_argument('--ingraph', action='store', nargs='+',
                       help=('parameters to slice into the graphs. '
                             'Defaults to None.'),
                       choices=['ff', 'model', 'substrings', 'POS'])
        p.add_argument('--no-positions', dest='positions',
                       action='store_const', const=False, default=True,
                       help="don't analyze positions of substitutions")
        p.add_argument('--no-paths', dest='paths', action='store_const',
                       const=False, default=True,
                       help="don't analyze path lengths of substitutions")
        p.add_argument('--save', dest='save', action='store_const',
                       const=True, default=False,
                       help='save figures to files')
        p.add_argument('--overwrite', dest='overwrite', action='store_const',
                       const=True, default=False,
                       help='overwrite existing figure files')
        p.add_argument('--no-show', dest='show', action='store_const',
                       const=False, default=True,
                       help=("don't show the graphs, just save the file. "
                             'This implies --save'))

        return p

    def print_analysis(self):
        """Print details of the analyses specified by the instance."""

        print
        print 'Analyzing with the following lists of args:'
        print '  ffs = {}'.format(self.ffs)
        print '  models = {}'.format(self.models)
        print '  substringss = {}'.format(self.substringss)
        print '  POSs = {}'.format(self.POSs)
        print '  ingraph slicing = {}'.format(self.ingraph)
        if self.has_fixedslicing_model():
            print '  n_timebagss = {}'.format(self.n_timebagss)
        print '  features = {}'.format(self.features)
        print '  positions = {}'.format(self.positions)
        print '  paths = {}'.format(self.paths)
        print '  save = {}'.format(self.save)
        print '  overwrite = {}'.format(self.overwrite)
        print '  show = {}'.format(self.show)
