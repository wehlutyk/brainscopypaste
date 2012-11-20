import argparse as ap

from datastructure.full import Cluster
from util import list_attributes_trunc
import settings as st


class MiningArgs(object):

    def __init__(self):

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
        #p.add_argument('--verbose', dest='verbose', action='store_const',
                    #const=True, default=False,
                    #help='print out the substitutions that are found')

        # Get the actual arguments.

        args = p.parse_args()

        self.ff = args.ff[0]
        self.model = args.model[0]
        self.substrings = bool(int(args.substrings[0]))
        self.POS = args.POS[0]
        self.resume = args.resume
        # FIXME: see if this is necessary
        self.verbose = False

        if self.is_fixedslicing_model():
            try:
                self.n_timebags = int(args.n_timebags[0])
            except:
                raise ValueError(("Need the 'n_timebags' argument when 'model' "
                                  "is one of {}.".format(st.memetracker_mining_fixedslicing_models)))

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
        # FIXME: print '  verbose = {}'.format(argset['verbose'])
        if self.is_fixedslicing_model():
            print '  n_timebags = {}'.format(self.n_timebags)
