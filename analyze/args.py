import re

from baseargs import BaseArgs, MultipleBaseArgs
import settings as st


class AnalysisArgs(BaseArgs):

    description = 'analyze substitutions (haming_word-distance == 1)'

    def __init__(self, init_dict=None):
        super(AnalysisArgs, self).__init__(init_dict)

        if init_dict is None:
            self.parse_features(self.args.features)
        else:
            self.parse_features(init_dict['features'])

    def parse_features(self, f_strings):

        self.features = {}

        if f_strings is None:
            for s in st.mt_analysis_features.iterkeys():
                self.features[s] = set(st.mt_analysis_features[s].keys())
            return

        if f_strings[0] == 'None':
            return

        try:

            for f_string in f_strings:

                try:
                    parts = re.split('_', f_string)
                    if not self.features.has_key(parts[0]):
                        self.features[parts[0]] = set([])
                    self.features[parts[0]].add(parts[1])
                except IndexError:
                    continue

            for s in self.features.iterkeys():
                if len(self.features[s]) == 0:
                    self.features[s] = set(st.mt_analysis_features[s].keys())

        except TypeError:
            pass

    def create_argparser(self):

        # Create the arguments parser.

        p = super(AnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t for s in st.mt_analysis_features.iterkeys()
                                 for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)

        return p

    def print_analysis(self):
        """Print this AnalysisArgs to stdout."""
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

    def title(self):
        title = 'ff: {} | model: {} | sub: {} | POS: {}'.format(self.ff,
                                                                self.model,
                                                                self.substrings,
                                                                self.POS)
        if self.is_fixedslicing_model():
            title += ' | n: {}'.format(self.n_timebags)
        title += '\n'
        return title


class MultipleAnalysisArgs(MultipleBaseArgs):

    description = 'analyze substitutions for various argument sets'

    def __init__(self):

        super(MultipleAnalysisArgs, self).__init__()

        self.features = self.args.features

    def create_init_dict(self, ff, model, substrings, POS):
        init_dict = super(MultipleAnalysisArgs,
                          self).create_init_dict(ff,
                                                 model,
                                                 substrings,
                                                 POS)
        init_dict['features'] = self.args.features
        return init_dict

    def create_args_instance(self, init_dict):
        return AnalysisArgs(init_dict)

    def create_argparser(self):

        # Create the arguments parser.

        p = super(MultipleAnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t for s in st.mt_analysis_features.iterkeys()
                                 for t in st.mt_analysis_features[s].iterkeys()] +
                    ['None'])
        p.add_argument('--features', action='store', nargs='+',
                       help='features to be analysed. Defaults to all.',
                       choices=features)

        return p

    def print_analysis(self):
        """Print this MultipleAnalysisArgs to stdout."""
        print
        print 'Analyzing with the following lists of args:'
        print '  ffs = {}'.format(self.ffs)
        print '  models = {}'.format(self.models)
        print '  substringss = {}'.format(self.substringss)
        print '  POSs = {}'.format(self.POSs)
        if self.has_fixedslicing_model():
            print '  n_timebagss = {}'.format(self.n_timebagss)
        print '  features = {}'.format(self.features)
