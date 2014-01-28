#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Argument classes for analysis of substitutions.

These classes are used to define arguments in the analysis scripts
(:mod:`analyze_substitutions` and :mod:`analyze_substitutions_multiple`)

"""


import re

import numpy as np

from baseargs import BaseArgs, MultipleBaseArgs
import settings as st


class AnalysisArgs(BaseArgs):

    """Arguments for analysis of one list of substitutions.

    It defines all necessary arguments for an analysis of mined substitutions,
    and is pluggable into most structures that are related to such an
    analysis. It is also the main object that :class:`MultipleAnalysisArgs`
    manipulates. This class inherits from :class:`baseargs.BaseArgs`.

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
        (``!show`` implies ``save``.)

    Methods
    -------
    create_argparser()
        Create the argument parser to extract arguments from command line.
    parse_features()
        Parse the ``features`` argument from the command line.
    print_analysis()
        Print details of the analysis specified by the instance.
    title()
        Build a title representing the type of analysis specified.

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
        """Parse the ``features`` argument from the command line.

        The result, a subportion of the dict of features defined by
        :mod:`settings`, is stored in ``self.features``.

        Parameters
        ----------
        f_strings : list of strings
            The ``features`` argument extracted from the command line.

        """

        self.features = {}

        if f_strings is None:
            for s in st.mt_analysis_features.iterkeys():
                self.features[s] = set(st.mt_analysis_features[s].keys())
            return

        if f_strings[0] == 'None':
            return

        try:

            for f_string in f_strings:

                parts = re.split('_', f_string)
                if not self.features.has_key(parts[0]):
                    self.features[parts[0]] = set([])
                if len(parts) > 1:
                    self.features[parts[0]].add('_'.join(parts[1:]))

            for s in self.features.iterkeys():
                if len(self.features[s]) == 0:
                    self.features[s] = set(st.mt_analysis_features[s].keys())

        # If ``f_strings`` is None
        except TypeError:
            pass

    def create_argparser(self):
        """Create the argument parser to extract arguments from command line.

        This method is used by :class:`~baseargs.BaseArgs`'s constructor.

        Returns
        -------
        p : :class:`argparse.ArgumentParser`
            The argument parser used to parse the command line arguments.

        """

        # Create the arguments parser.

        p = super(AnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t for s in st.mt_analysis_features.iterkeys()
                                 for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)
        p.add_argument('--no-positions', dest='positions', action='store_const',
                       const=False, default=True,
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

    def __init__(self, aas, maa, s):
        self.aas = aas
        self.save = maa.save

        # Build texts for filenames
        self.ffs_text = ','.join(maa.ffs) if s[0] is Ellipsis else maa.ffs[s[0]]
        self.models_text = ','.join(maa.models) if s[1] is Ellipsis else maa.models[s[1]]
        if s[2] is Ellipsis:
            self.substringss_text = ','.join(['yes' if ss else 'no' for ss in maa.substringss])
        else:
            self.substringss_text = 'yes' if maa.substringss[s[2]] else 'no'
        self.POSs_text = ','.join(maa.POSs) if s[3] is Ellipsis else maa.POSs[s[3]]

        fixedslicing_models = [aa.is_fixedslicing_model() for aa in aas]
        if sum(fixedslicing_models):
            self.has_fixedslicing_model = True
            self.n_timebags_text = aas[fixedslicing_models.index(True)].n_timebags

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
        for aa in self.aas:
            yield aa

    def title(self):
        """Build a title representing the type of analysis specified.

        Returns
        -------
        title : string
            The built title.

        """

        title = 'ff: {} | model: {} | sub: {} | POS: {}'.format(self.ffs_text,
                                                                self.models_text,
                                                                self.substringss_text,
                                                                self.POSs_text)
        if self.has_fixedslicing_model:
            title += ' | n: {}'.format(self.n_timebags_text)
        return title


class MultipleAnalysisArgs(MultipleBaseArgs):

    """Arguments for analysis of multiple lists of substitutions.

    It defines all necessary arguments for analysis of substitutions mined
    with several sets of arguments, and is usable with the
    :class:`.base.SubstitutionsAnalyzer`. This class inherits from
    :class:`baseargs.MultipleBaseArgs`.

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
        (``!show`` implies ``save``.)

    Methods
    -------
    create_argparser()
        Create the argument parser to extract arguments from command line.
    create_args_instance()
        Create a :class:`AnalysisArgs` instance.
    create_init_dict()
        Create an initialization dict.
    print_analysis()
        Print details of the analyses specified by the instance.

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
        self.ingraph_c = {'ff', 'model', 'substrings', 'POS'}.difference(self.ingraph)
        self.build_aas_ndarray()

    def __iter__(self):
        # Create the list of slicing tuples
        slices = set()
        for ff_idx in range(len(self.ffs)):
            for model_idx in range(len(self.models)):
                for substrings_idx in range(len(self.substringss)):
                    for POS_idx in range(len(self.POSs)):
                        s = ()
                        s += (ff_idx if 'ff' in self.ingraph_c else Ellipsis,)
                        s += (model_idx if 'model' in self.ingraph_c else Ellipsis,)
                        s += (substrings_idx if 'substrings' in self.ingraph_c else Ellipsis,)
                        s += (POS_idx if 'POS' in self.ingraph_c else Ellipsis,)
                        slices.add(s)

        for s in slices:
            y = self.aas_ndarray[s]
            if isinstance(y, np.ndarray):
                yield GroupAnalysisArgs(y.flatten(), self, s)
            else:
                yield GroupAnalysisArgs([y], self, s)

    def build_aas_ndarray(self):
        self.aas_shape = (len(self.ffs), len(self.models), len(self.substringss), len(self.POSs))
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
                                raise ValueError("can't have multiple n_timebags values when using --ingraph option")

                            init_dict['n_timebags'] = int(self.n_timebagss[0])
                            self.aas_ndarray[i,j,k,l] = self.create_args_instance(init_dict)

                        else:

                            self.aas_ndarray[i,j,k,l] = self.create_args_instance(init_dict)


    def create_init_dict(self, ff, model, substrings, POS):
        """Create an initialization dict.

        This will produce an initialization dict suitable for creation of
        an instance of :class:`AnalysisArgs`, merging the parameters provided
        and the arguments stored in attributes of ``self``.

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
                          self).create_init_dict(ff,
                                                 model,
                                                 substrings,
                                                 POS)
        init_dict['features'] = self.args.features
        init_dict['positions'] = self.args.positions
        init_dict['paths'] = self.args.paths
        init_dict['save'] = self.args.save
        init_dict['overwrite'] = self.args.overwrite
        init_dict['show'] = self.args.show
        return init_dict

    def create_args_instance(self, init_dict):
        """Create a :class:`AnalysisArgs` instance.

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
        p : :class:`argparse.ArgumentParser`
            The argument parser used to parse the command line arguments.

        """

        # Create the arguments parser.

        p = super(MultipleAnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t for s in st.mt_analysis_features.iterkeys()
                                 for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)
        p.add_argument('--ingraph', action='store', nargs='+',
                       help='parameters to slice into the graphs. Defaults to None.',
                       choices=['ff', 'model', 'substrings', 'POS'])
        p.add_argument('--no-positions', dest='positions', action='store_const',
                       const=False, default=True,
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
