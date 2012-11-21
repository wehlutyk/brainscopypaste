from baseargs import BaseArgs, MultipleBaseArgs


class AnalysisArgs(BaseArgs):

    description = 'analyze substitutions (haming_word-distance == 1)'

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


class MultipleAnalysisArgs(MultipleBaseArgs):

    description = 'analyze substitutions for various argument sets'

    def create_args_instance(self, init_dict):
        return AnalysisArgs(init_dict)
