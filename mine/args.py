import argparse as ap

from datastructure.full import Cluster
from util import list_attributes_trunc
import settings as st


class MiningArgs(object):

    def __init__(self, init_dict=None):

        if init_dict is None:

            args = self.parse_args()

            self.ff = args.ff[0]
            self.model = args.model[0]
            self.substrings = bool(int(args.substrings[0]))
            self.POS = args.POS[0]
            self.resume = args.resume
            # FIXME: see if this is necessary
            self.verbose = args.verbose
            self.set_n_timebags(args)

        else:

            self.ff = init_dict['ff']
            self.model = init_dict['model']
            self.substrings = init_dict['substrings']
            self.POS = init_dict['POS']
            self.resume = init_dict['resume']
            # FIXME: see if this is necessary
            self.verbose = False
            self.set_n_timebags(init_dict)

    def parse_args(self):
        # Create the arguments parser.

        p = ap.ArgumentParser(description=('mine substitutions '
                                        '(hamming_word-distance == 1)'))

        p.add_argument('--ff', action='store', nargs=1, required=True,
                    help=('Specify on what dataset the mining is done: '
                            "'full': the full clusters; "
                            "'framed': the framed clusters; "
                            "'filtered': the filtered clusters; "
                            "'ff': the framed-filtered clusters."),
                    choices=['full', 'framed', 'filtered', 'ff'])
        p.add_argument('--model', action='store', nargs=1, required=True,
                    help=('mine substitutions from the root quote, from '
                            'successive timebags, or based on the appearance '
                            "times of quotes. 'root': from root; 'tbgs': "
                            "from successive timebags; 'cumtbgs': from "
                            "cumulated timebags; 'time': based on "
                            "appearance times. 'slidetbgs': based on the "
                            "previous timebag. 'growtbgs': based on the "
                            'previous cumulated timebag.'),
                    choices=list_attributes_trunc(Cluster, 'iter_substitutions_'))
        p.add_argument('--substrings', action='store', nargs=1, required=True,
                    help=('1: include substrings as accepted substitutions'
                            "0: don't include substrings (i.e. only strings of "
                            'the same length.'),
                    choices=['0', '1'])
        p.add_argument('--POS', action='store', nargs=1, required=True,
                    help=('select what POS to analyze. Valid values are '
                            "'a', 'n', 'v', 'r', or 'all' (in which case only "
                            'substitutions where words have the same POS are '
                            'taken into account).'),
                    choices=st.memetracker_subst_POSs)
        p.add_argument('--n_timebags', action='store', nargs=1, required=False,
                    help=('number of timebags to slice the clusters into. '
                        'This is only necessary if the model is one '
                        'of {}.'.format(st.memetracker_mining_fixedslicing_models)))
        p.add_argument('--resume', dest='resume', action='store_const',
                    const=True, default=False, help='resume a previous mining')
        p.add_argument('--verbose', dest='verbose', action='store_const',
                    const=True, default=False,
                    help='print out the substitutions that are found')

        # Get the actual arguments.

        return p.parse_args()

    def set_n_timebags(self, args_or_dict):

        if self.is_fixedslicing_model():
            try:
                if type(args_or_dict) == dict:
                    self.n_timebags = args_or_dict['n_timebags']
                else:
                    self.n_timebags = int(args_or_dict.n_timebags[0])

                if self.n_timebags < 2:
                    raise ValueError(("The requested 'n_timebags' must be at least 2 for a model "
                                     "in {}.".format(st.memetracker_mining_fixedslicing_models)))
            except (KeyError, AttributeError):
                raise ValueError(("Need the 'n_timebags' argument when 'model' "
                                  "is one of {}.".format(st.memetracker_mining_fixedslicing_models)))

        else:
            # This will be ignored during mining, but must be present
            self.n_timebags = 0

    def is_fixedslicing_model(self):
        return self.model in st.memetracker_mining_fixedslicing_models

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


class MultipleMiningArgs(object):

    def __init__(self):

        args = self.parse_args()

        self.ffs = args.ffs
        self.models = args.models
        self.substringss = [bool(s) for s in args.substringss]
        self.POSs = args.POSs
        self.set_n_timebagss(args)
        self.resume = args.resume
        self.multi_thread = args.multi_thread

        self.mas = []

        for ff in args.ffs:

            for model in args.models:

                for substrings in args.substringss:

                    for POS in args.POSs:

                        init_dict = {'ff': ff,
                                     'model': model,
                                     'substrings': bool(substrings),
                                     'POS': POS,
                                     'resume': args.resume}

                        if model in st.memetracker_mining_fixedslicing_models:

                            for n_timebags in args.n_timebagss:

                                init_dict['n_timebags'] = int(n_timebags)
                                self.mas.append(MiningArgs(init_dict))

                        else:

                            self.mas.append(MiningArgs(init_dict))

    def __iter__(self):
        for ma in self.mas:
            yield ma

    def __len__(self):
        return len(self.mas)

    def has_fixedslicing_model(self):
        return not set(self.models).isdisjoint(set(st.memetracker_mining_fixedslicing_models))

    def set_n_timebagss(self, args):
        if self.has_fixedslicing_model():
            try:
                self.n_timebagss = [int(n) for n in args.n_timebagss]
            except TypeError:
                raise ValueError(("Need the 'n_timebagss' argument when 'models' "
                                  "has one of {}.".format(st.memetracker_mining_fixedslicing_models)))

    def parse_args(self):

        # Create the arguments parser.

        p = ap.ArgumentParser(description=('mine substitutions for multiple '
                                            'argument sets'))
        p.add_argument('--ffs', action='store', nargs='+', required=True,
                    help=('space-separated list of datasets on which the '
                            'mining is done: '
                            "'full': the full clusters; "
                            "'framed': the framed clusters; "
                            "'filtered': the filtered clusters; "
                            "'ff': the framed-filtered clusters."),
                    choices=['full', 'framed', 'filtered', 'ff'])
        p.add_argument('--models', action='store', nargs='+',
                    required=True,
                    help=('mine substitutions from the root quote, from '
                            'successive timebags, or based on the appearance '
                            "times of quotes. 'root': from root; 'tbgs': "
                            "from successive timebags; 'cumtbgs': from "
                            "cumulated timebags; 'time': based on "
                            'appearance times. This should be a space-'
                            'separated list of such arguments.'),
                    choices=list_attributes_trunc(Cluster, 'iter_substitutions_'))
        p.add_argument('--substringss', action='store', nargs='+', required=True,
                    help=('1: include substrings as accepted substitutions'
                            "0: don't include substrings (i.e. only strings of "
                            'the same length. This should be a space-separated '
                            'list of such arguments.'),
                    choices=['0', '1'])
        p.add_argument('--POSs', action='store', nargs='+', required=True,
                    help=('space-seperated list of POS tags to examine. Valid'
                            "values are 'a', 'n', 'v', 'r', or 'all' (in which"
                            'case only substitutions where words have the same '
                            'POS are taken into account).'),
                    choices=st.memetracker_subst_POSs)
        p.add_argument('--n_timebagss', action='store', nargs='+',
                    help=('space-separated list of timebag slicings to '
                            "examine. e.g. '2 3 4' will run the mining "
                            'slicing clusters in 2, then 3, then 4 '
                            'timebags, and examining all possible transitions '
                            'each time. This parameter is ignored for non fixed-'
                            'slicings models (i.e. a model not in '
                            '{})'.format(st.memetracker_mining_fixedslicing_models)))
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

        # Get the actual arguments.

        return p.parse_args()

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
