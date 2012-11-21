import re

from baseargs import BaseArgs#, MultipleBaseArgs
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

        if len(self.features) == 0:
            for s in st.mt_analysis_features.iterkeys():
                self.features[s] = set(st.mt_analysis_features[s].keys())

    def create_argparser(self):

        # Create the arguments parser.

        p = super(AnalysisArgs, self).create_argparser()
        features = ([s for s in st.mt_analysis_features.iterkeys()] +
                    [s + '_' + t for s in st.mt_analysis_features.iterkeys()
                                 for t in st.mt_analysis_features[s].iterkeys()])
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


#class MultipleAnalysisArgs(MultipleBaseArgs):

    #description = 'analyze substitutions for various argument sets'

    #def create_args_instance(self, init_dict):
        #return AnalysisArgs(init_dict)
