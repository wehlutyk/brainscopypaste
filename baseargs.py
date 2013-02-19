import argparse as ap

from datastructure.full import Cluster
from util.generic import list_attributes_trunc
import settings as st


class BaseArgs(object):

    description='(not filled)'

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
                    help=('Specify the model with which the operation is done. '
                          'Must be one of {}.'.format(models)),
                    choices=models)
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
                       choices=st.mt_mining_POSs)
        p.add_argument('--n_timebags', action='store', nargs=1, required=False,
                        help=('number of timebags to slice the clusters into. '
                              'This is only necessary if the model is one '
                              'of {}.'.format(st.mt_mining_fixedslicing_models)))

        return p

    def set_n_timebags(self, init_dict=None):

        if self.is_fixedslicing_model():
            try:
                if not init_dict is None:
                    self.n_timebags = init_dict['n_timebags']
                else:
                    self.n_timebags = int(self.args.n_timebags[0])

                if self.n_timebags < 2:
                    raise ValueError(("The requested 'n_timebags' must be at least 2 for a model "
                                     "in {}.".format(st.mt_mining_fixedslicing_models)))
            except (KeyError, TypeError):
                raise ValueError(("Need the 'n_timebags' argument when 'model' "
                                  "is one of {}.".format(st.mt_mining_fixedslicing_models)))

        else:
            # This will be ignored during mining, but must be present
            self.n_timebags = 0

    def is_fixedslicing_model(self):
        return self.model in st.mt_mining_fixedslicing_models


class MultipleBaseArgs(object):

    description = '(not filled)'

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
                                self.alist.append(self.create_args_instance(init_dict))

                        else:

                            self.alist.append(self.create_args_instance(init_dict))

    def __iter__(self):
        for a in self.alist:
            yield a

    def __len__(self):
        return len(self.alist)

    def has_fixedslicing_model(self):
        return not set(self.models).isdisjoint(set(st.mt_mining_fixedslicing_models))

    def set_n_timebagss(self):
        if self.has_fixedslicing_model():
            try:
                self.n_timebagss = [int(n) for n in self.args.n_timebagss]
            except TypeError:
                raise ValueError(("Need the 'n_timebagss' argument when 'models' "
                                  "has one of {}.".format(st.mt_mining_fixedslicing_models)))

    def create_init_dict(self, ff, model, substrings, POS):
        return {'ff': ff, 'model': model, 'substrings': bool(int(substrings)), 'POS': POS}

    def create_args_instance(self, init_dict):
        return BaseArgs(init_dict)

    def create_argparser(self):

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
                       help=('do the operation using these models. Space separated list '
                             'of elements from {}.'.format(models)),
                       choices=models)
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
                       choices=st.mt_mining_POSs)
        p.add_argument('--n_timebagss', action='store', nargs='+',
                       help=('space-separated list of timebag slicings to '
                             "examine. e.g. '2 3 4' will run the mining "
                             'slicing clusters in 2, then 3, then 4 '
                             'timebags, and examining all possible transitions '
                             'each time. This parameter is ignored for non fixed-'
                             'slicings models (i.e. a model not in '
                             '{})'.format(st.mt_mining_fixedslicing_models)))

        return p
