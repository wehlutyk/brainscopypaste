#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Argument classes for analysis of substitutions.

These classes are used to define arguments in the analysis scripts
(:mod:`analyze_substitutions` and :mod:`analyze_substitutions_multiple`)

"""


import re

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

    def title(self):
        """Build a title representing the type of analysis specified.

        Returns
        -------
        title : string
            The built title.

        """

        title = 'ff: {} | model: {} | sub: {} | POS: {}'.format(self.ff,
                                                                self.model,
                                                                self.substrings,
                                                                self.POS)
        if self.is_fixedslicing_model():
            title += ' | n: {}'.format(self.n_timebags)
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
        self.positions = self.args.positions
        self.paths = self.args.paths
        self.save = self.args.save
        self.overwrite = self.args.overwrite
        self.show = self.args.show

        # No show implies save
        self.save = self.save or (not self.show)

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
        if self.has_fixedslicing_model():
            print '  n_timebagss = {}'.format(self.n_timebagss)
        print '  features = {}'.format(self.features)
        print '  positions = {}'.format(self.positions)
        print '  paths = {}'.format(self.paths)
        print '  save = {}'.format(self.save)
        print '  overwrite = {}'.format(self.overwrite)
        print '  show = {}'.format(self.show)
