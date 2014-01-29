from __future__ import division

from baseargs import BaseArgs, MultipleBaseArgs


class MiningArgs(BaseArgs):

    description = 'mine substitutions (haming_word-distance == 1)'

    def __init__(self, init_dict=None):

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

        # Create the arguments parser.

        p = super(MiningArgs, self).create_argparser()
        p.add_argument('--resume', dest='resume', action='store_const',
                       const=True, default=False, help='resume a previous mining')
        p.add_argument('--verbose', dest='verbose', action='store_const',
                       const=True, default=False,
                       help='print out the substitutions that are found')

        return p

    def print_mining(self):
        """Print this MiningArgs to stdout."""
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

    description = 'mine substitutions for various argument sets'

    def __init__(self):

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
                             'script finds some files it was supposed to create, '
                             'it will just skip the corresponding mining and '
                             'continue with the rest. Otherwise it will abort.'))
        p.add_argument('--no-multi-thread', dest='multi_thread',
                       action='store_const', const=False, default=True,
                       help=('deactivate multi-threading (default: multi-thread '
                             'to use all processors but one)'))

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
