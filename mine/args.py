#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Argument structures to define parameters for mining substitutions.

Mining for substitutions involves several steps, each of which can be tweaked,
activated, or de-activated. The base set of arguments is defined in
:mod:`baseargs`, and you should start by reading the explanation on that page.
Here we merely three arguments: `verbose` (print more information while
mining), `resume` (do not mine again data that has already been saved to
files), and possibility for multithreading in the case of multiple sets of
mining arguments.

"""


from __future__ import division

from baseargs import BaseArgs, MultipleBaseArgs


class MiningArgs(BaseArgs):

    """Single set of arguments for mining substitutions.

    Parameters
    ----------
    init_dict : dict, optional
        If provided, must be a dict of arguments as specified for
        :class:`~baseargs.BaseArgs`, defining the mining arguments to use;
        defaults to `None`, in which case the arguments are taken from the
        command line.

    Attributes
    ----------
    description : string
    resume : bool
        Whether or not to skip mining for data that has already been saved
        to files.
    verbose : bool
        Whether or not to print detailed information, step by step, about the
        substitutions encountered.

    See Also
    --------
    baseargs.BaseArgs, MultipleMiningArgs, .substitutions.SubstitutionsMiner

    """

    #: Description of the command given on the command line.
    description = 'mine substitutions (haming_word-distance == 1)'

    def __init__(self, init_dict=None):
        """Initialize the structure either from `init_dict` or the command
        line.

        Parameters
        ----------
        init_dict : dict, optional
            If provided, must be a dict of arguments as specified for
            :class:`~baseargs.BaseArgs`, defining the mining arguments to use;
            defaults to `None`, in which case the arguments are taken from the
            command line.

        """

        super(MiningArgs, self).__init__(init_dict)

        # Extend the structure with whatever we added in argparser

        if init_dict is None:

            self.resume = self.args.resume
            # FIXME: see if this is necessary
            self.verbose = self.args.verbose

        else:

            self.resume = init_dict['resume']
            # FIXME: see if this is necessary
            self.verbose = False

    def create_argparser(self):
        """Extend :class:`~baseargs.BaseArgs`'s argparser with `resume` and
        `verbose`.

        Returns
        -------
        ArgumentParser
            The :class:`~argparse.ArgumentParser` instance to parse the
            command line.

        """

        # Create the arguments parser.

        p = super(MiningArgs, self).create_argparser()
        p.add_argument('--resume', dest='resume', action='store_const',
                       const=True, default=False,
                       help='resume a previous mining')
        p.add_argument('--verbose', dest='verbose', action='store_const',
                       const=True, default=False,
                       help='print out the substitutions that are found')

        return p

    def print_mining(self):
        """Print details about this `MiningArgs` to stdout."""

        print
        print 'Mining with the following args:'
        print '  ff = {}'.format(self.ff)
        print '  model = {}'.format(self.model)
        print '  substrings = {}'.format(self.substrings)
        print '  POS = {}'.format(self.POS)
        if self.is_fixedslicing_model():
            print '  n_timebags = {}'.format(self.n_timebags)
        print '  resume = {}'.format(self.resume)
        print '  verbose = {}'.format(self.verbose)


class MultipleMiningArgs(MultipleBaseArgs):

    """Multiple sets of arguments for mining substitutions in one command.

    There are many combinations of mining arguments, and it can come in useful
    to mine with many different arguments sets in one go, even multithreading
    the mining. This class extracts arguments from the command line for such a
    situation. It inherits from :class:`~baseargs.MultipleBaseArgs` and adds
    the possibility for resuming previous mining and multithreading.

    Parameters
    ----------
    bla : bli
        Blou.

    Attributes
    ----------
    description : string
    resume : bool
        Whether or not to skip mining with arguments for which data has \
        already been saved to files.
    multi_th* : bool
        Whether or not to use multiple cores when mining with different sets \
        of arguments at the same time (misnomer: this is in fact \
            multiprocessing, not multithreading) (**note**: the attribute is \
            `multi_thread`, but for some reason numpydoc doesn't allow an \
            attibute name to be more than 9 characters).

    See Also
    --------
    MiningArgs, baseargs.MultipleBaseArgs, .substitutions.SubstitutionsMiner

    """

    #: Description of the command given on the command line.
    description = 'mine substitutions for various argument sets'

    def __init__(self):
        """Initialize the structure with arguments from the command line."""

        super(MultipleMiningArgs, self).__init__()

        self.resume = self.args.resume
        self.multi_thread = self.args.multi_thread

    def create_init_dict(self, ff, model, substrings, POS):
        init_dict = super(MultipleMiningArgs,
                          self).create_init_dict(ff,
                                                 model,
                                                 substrings,
                                                 POS)
        init_dict['resume'] = self.args.resume
        return init_dict

    def create_args_instance(self, init_dict):
        return MiningArgs(init_dict)

    def create_argparser(self):

        # Create the arguments parser.

        p = super(MultipleMiningArgs, self).create_argparser()
        p.add_argument('--resume', dest='resume',
                       action='store_const', const=True, default=False,
                       help=('resume a previously interrupted mining: if the '
                             'script finds some files it was supposed to '
                             'create, it will just skip the corresponding '
                             'mining and continue with the rest. Otherwise it '
                             'will abort.'))
        p.add_argument('--no-multi-thread', dest='multi_thread',
                       action='store_const', const=False, default=True,
                       help=('deactivate multi-threading (default: '
                             'multi-thread to use all processors but one)'))

        return p

    def print_mining(self):
        """Print this MultipleMiningArgs to stdout."""
        print
        print 'Mining with the following lists of args:'
        print '  ffs = {}'.format(self.ffs)
        print '  models = {}'.format(self.models)
        print '  substringss = {}'.format(self.substringss)
        print '  POSs = {}'.format(self.POSs)
        if self.has_fixedslicing_model():
            print '  n_timebagss = {}'.format(self.n_timebagss)
        print '  resume = {}'.format(self.resume)
        print '  multi-thread = {}'.format(self.multi_thread)
