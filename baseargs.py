#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base classes from which all argument classes derive.

The classes in this module define the common arguments present in both
analysis and mining (see :mod:`analyze.args` and :mod:`mine.args`).

"""


from __future__ import division

import argparse as ap

from datastructure.full import Cluster
from util.generic import list_attributes_trunc
import settings as st


class BaseArgs(object):

    """Base class for all single-set argument classes.

    This class defines an :class:`~argparse.ArgumentParser` that can later be
    extended by subclasses, tailoring it to analysis or mining needs.

    There are four main parameters (and one optional parameter) defining what
    this argument set looks like. These parameters are also used in all
    subclasses defining arguments, and are the following:

    * `ff`: type of `framing-filtering` that is chosen for the base cluster
        data. This defines which framed or filtered set of clusters will be
        used. Accepted values are `full`, `framed`, `filtered`, `ff` (meaning
        both framed and filtered).
    * `model`: type of source-destination reconstruction model to be used.
        Accepted values are `tbgs`, `root`, `cumtbgs`, `slidetbags`,
        `growtbgs`, and `time`.
    * `substrings`: whether or not substitutions from substrings are to be
        considered (i.e. substitutions that involve two steps: cropping then
        substituting, as opposed to simply substituting). Can be either
        ``True`` or ``False`` (1 or 0 on the command line).
    * `POS`: how to consider POS tags: whether to check for simple
        correspondence between source and destination words in substitutions,
        or to filter further and remove all substitutions involving words that
        don't fit a specified POS tag. Can be any of `all`, `a`, `n`, `v`, `r`.
    * `n_timebags`: in case the `model` involves slicing clusters into timebags
        of a fixed length (usually a fraction of the duration of the cluster
        itself), this parameters specifies in how many parts each cluster is
        to be sliced to produce the timebags. Can be any integer greater or
        equal to two.

    Parameters
    ----------
    init_dict : dict, optional
        If absent, arguments are collected from the command line; if present,
        this must be a dict whose keys are `ff`, `model`, `substrings`, `POS`,
        and possibly `n_timebags` if `model` specifies a fixed-slicing model.

    Attributes
    ----------
    description
    args : namespace
        The namespace of args extracted from the command-line if `init_dict` \
        was `None`.
    ff : string
        The `ff` argument from the command line or from `init_dict`.
    model : string
        The `model` argument from the command line or from `init_dict`.
    substrings : bool
        The `substrings` argument from the command line or from `init_dict`.
    POS : string
        The `POS` argument from the command line or from `init_dict`.
    n_timebags : int
        0 if `model` isn't a fixed-slicing model; otherwise, the number of
        timebags specified at the command line or in `init_dict`.

    See Also
    --------
    MultipleBaseArgs, analyze.args.AnalysisArgs, mine.args.MiningArgs

    """

    description = '(not filled)'
    """Description of the command for the help screen at the command-line;
    meant to be filled in by subclasses."""

    def __init__(self, init_dict=None):

        if init_dict is None:

            self.args = self.create_argparser().parse_args()

            self.ff = self.args.ff[0]
            self.model = self.args.model[0]
            self.substrings = bool(int(self.args.substrings[0]))
            self.POS = self.args.POS[0]
            self.set_n_timebags()

        else:

            self.ff = init_dict['ff']
            self.model = init_dict['model']
            self.substrings = init_dict['substrings']
            self.POS = init_dict['POS']
            self.set_n_timebags(init_dict)

    def create_argparser(self):
        """Create the :class:`~argparse.ArgumentParser` that can parse our
        base arguments.

        Returns
        -------
        ArgumentParser
            The created argument parser, which can be further extended by
            subclasses.

        """

        # Create the arguments parser.

        p = ap.ArgumentParser(description=self.description)

        p.add_argument('--ff', action='store', nargs=1, required=True,
                       help=('Specify on what dataset the operation is done: '
                             "'full': the full clusters; "
                             "'framed': the framed clusters; "
                             "'filtered': the filtered clusters; "
                             "'ff': the framed-filtered clusters."),
                       choices=['full', 'framed', 'filtered', 'ff'])
        models = list_attributes_trunc(Cluster, 'iter_substitutions_')
        p.add_argument('--model', action='store', nargs=1, required=True,
                       help=('Specify the model with which the operation is '
                             'done. Must be one of {}.'.format(models)),
                       choices=models)
        p.add_argument('--substrings', action='store', nargs=1, required=True,
                       help=('1: include substrings as accepted substitutions'
                             "0: don't include substrings (i.e. only strings "
                             'of the same length.'),
                       choices=['0', '1'])
        p.add_argument('--POS', action='store', nargs=1, required=True,
                       help=('select what POS to analyze. Valid values are '
                             "'a', 'n', 'v', 'r', or 'all' (in which case "
                             'only substitutions where words have the same '
                             'POS are taken into account).'),
                       choices=st.mt_mining_POSs)
        p.add_argument('--n_timebags', action='store', nargs=1, required=False,
                       help=('number of timebags to slice the clusters into. '
                             'This is only necessary if the model is one of '
                             '{}.'.format(st.mt_mining_fixedslicing_models)))

        return p

    def set_n_timebags(self, init_dict=None):
        """Set the `n_timebags` attribute depending from where it was provided.

        If `self.model` specifies a non fixed-slicing model, `self.n_timebags`
        is set to 0. Otherwise it is taken from the command line or from
        `init_dict` if provided.

        Parameters
        ----------
        init_dict : dict, optional
            The optional initialization dict passed to this class's
            constructor.

        """

        if self.is_fixedslicing_model():
            try:
                if not init_dict is None:
                    self.n_timebags = init_dict['n_timebags']
                else:
                    self.n_timebags = int(self.args.n_timebags[0])

                if self.n_timebags < 2:
                    raise ValueError(
                        "The requested 'n_timebags' must be at least 2 for a "
                        "model in {}.".format(
                            st.mt_mining_fixedslicing_models))
            except (KeyError, TypeError):
                raise ValueError(
                    "Need the 'n_timebags' argument when 'model' is one of "
                    "{}.".format(st.mt_mining_fixedslicing_models))

        else:
            # This will be ignored during mining, but must be present
            self.n_timebags = 0

    def is_fixedslicing_model(self):
        """Whether or not `self.model` specifies a fixed-slicing model
        (returns a bool)."""

        return self.model in st.mt_mining_fixedslicing_models


class MultipleBaseArgs(object):

    """A arrayed version of :class:`BaseArgs`, allowing to specify multiple
    :class:`BaseArgs` at once.

    The class gets all its attributes and arguments from the command-line.
    Each parameter is essentially a plural form of the parameters for
    :class:`BaseArgs`, and the class will then build an array of all possible
    combinations of the values given for those parameters.

    Attributes
    ----------
    args : namespace
        The arguments parsed from the command line.
    ffs : list of strings
        List of values for the `ff` argument.
    models : list of strings
        List of values for the `model` argument.
    substringss : list of bools
        List of values for the `substrings` argument.
    POSs : list of strings
        List of values for the `POS` argument.
    n_timebagss : list of ints
        List of values for the `n_timebags` argument.
    alist : list of :class:`BaseArgs`
        The computed list of all argument sets, covering all possible
        combinations of the above attributes.

    See Also
    --------
    BaseArgs, analyze.args.MultipleAnalysisArgs, mine.args.MultipleMiningArgs

    """

    description = '(not filled)'
    """Description of the command for the help screen at the command-line;
    meant to be filled in by subclasses."""

    def __init__(self):

        self.args = self.create_argparser().parse_args()

        self.ffs = self.args.ffs
        self.models = self.args.models
        self.substringss = [bool(int(s)) for s in self.args.substringss]
        self.POSs = self.args.POSs
        self.set_n_timebagss()

        self.alist = []

        for ff in self.args.ffs:

            for model in self.args.models:

                for substrings in self.args.substringss:

                    for POS in self.args.POSs:

                        init_dict = self.create_init_dict(ff,
                                                          model,
                                                          substrings,
                                                          POS)

                        if model in st.mt_mining_fixedslicing_models:

                            for n_timebags in self.args.n_timebagss:

                                init_dict['n_timebags'] = int(n_timebags)
                                self.alist.append(
                                    self.create_args_instance(init_dict))

                        else:

                            self.alist.append(
                                self.create_args_instance(init_dict))

    def __iter__(self):
        """Iterate over all the argument sets in these
        :class:`MultipleBaseArgs`."""

        for a in self.alist:
            yield a

    def __len__(self):
        """Number of argument sets in these :class:`MultipleBaseArgs`."""

        return len(self.alist)

    def has_fixedslicing_model(self):
        """Whether or not there is at least one fixed-slicing model
        in our argument sets (returns a bool)."""

        return not set(self.models).isdisjoint(
            set(st.mt_mining_fixedslicing_models))

    def set_n_timebagss(self):
        """Set the `n_timebagss` attribute from command-line arguments."""

        if self.has_fixedslicing_model():
            try:
                self.n_timebagss = [int(n) for n in self.args.n_timebagss]
            except TypeError:
                raise ValueError(
                    "Need the 'n_timebagss' argument when 'models' has one of "
                    "{}.".format(st.mt_mining_fixedslicing_models))

    def create_init_dict(self, ff, model, substrings, POS):
        """Create an initialization dict for later creation of an individual
        argument set.

        This method is meant to be overridden by subclasses that need an
        extended initialization dict for their extended argument set.

        Parameters
        ----------
        ff : string
            The `ff` parameter from :class:`BaseArgs`.
        model : string
            The `model` parameter from :class:`BaseArgs`.
        substrings : bool
            The `substrings` parameter from :class:`BaseArgs`.
        POS : string
            The `POS` parameter from :class:`BaseArgs`.

        Returns
        -------
        dict
            An initialization dict to be passed to an argument set constructor.

        See Also
        --------
        mine.args.MultipleMiningArgs.create_init_dict,
        analyze.args.MultipleAnalysisArgs.create_init_dict

        """

        return {'ff': ff, 'model': model,
                'substrings': bool(int(substrings)), 'POS': POS}

    def create_args_instance(self, init_dict):
        """Create an argument set instance.

        This method is meant to be overridden by subclasses that need their
        argument sets to be instances of a subclass of :class:`BaseArgs`.

        Parameters
        ----------
        init_dict : dict
            The initialization dict passed to the argument set constructor.

        See Also
        --------
        mine.args.MultipleMiningArgs.create_args_instance,
        analyze.args.MultipleAnalysisArgs.create_args_instance

        """

        return BaseArgs(init_dict)

    def create_argparser(self):
        """Create the :class:`~argparse.ArgumentParser` that can parse our
        multiple arguments.

        Returns
        -------
        ArgumentParser
            The created argument parser, which can be further extended by
            subclasses.

        """

        # Create the arguments parser.

        p = ap.ArgumentParser(description=self.description)
        p.add_argument('--ffs', action='store', nargs='+', required=True,
                       help=('space-separated list of datasets on which the '
                             'operation is done: '
                             "'full': the full clusters; "
                             "'framed': the framed clusters; "
                             "'filtered': the filtered clusters; "
                             "'ff': the framed-filtered clusters."),
                       choices=['full', 'framed', 'filtered', 'ff'])
        models = list_attributes_trunc(Cluster, 'iter_substitutions_')
        p.add_argument('--models', action='store', nargs='+',
                       required=True,
                       help=('do the operation using these models. Space '
                             'separated list of elements from '
                             '{}.'.format(models)),
                       choices=models)
        p.add_argument('--substringss', action='store', nargs='+',
                       required=True,
                       help=('1: include substrings as accepted substitutions'
                             "0: don't include substrings (i.e. only strings "
                             'of the same length. This should be a space-'
                             'separated list of such arguments.'),
                       choices=['0', '1'])
        p.add_argument('--POSs', action='store', nargs='+', required=True,
                       help=('space-seperated list of POS tags to examine. '
                             "Valid values are 'a', 'n', 'v', 'r', or 'all' "
                             '(in which case only substitutions where words '
                             'have the same POS are taken into account).'),
                       choices=st.mt_mining_POSs)
        p.add_argument('--n_timebagss', action='store', nargs='+',
                       help=('space-separated list of timebag slicings to '
                             "examine. e.g. '2 3 4' will run the mining "
                             'slicing clusters in 2, then 3, then 4 '
                             'timebags, and examining all possible '
                             'transitions each time. This parameter is '
                             'ignored for non fixed-slicings models '
                             '(i.e. a model not in '
                             '{})'.format(st.mt_mining_fixedslicing_models)))

        return p
