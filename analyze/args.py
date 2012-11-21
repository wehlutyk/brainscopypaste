from baseargs import BaseArgs, MultipleBaseArgs


class AnalysisArgs(BaseArgs):

    description = 'analyze substitutions (haming_word-distance == 1)'


class MultipleAnalysisArgs(MultipleBaseArgs):

    description = 'analyze substitutions for various argument sets'

    def create_args_instance(self, init_dict):
        return AnalysisArgs(init_dict)
