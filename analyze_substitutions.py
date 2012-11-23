import pylab as pl

from analyze.args import AnalysisArgs
from analyze.substitutions import SubstitutionsAnalyzer


if __name__ == '__main__':
    analysis_args = AnalysisArgs()
    sa = SubstitutionsAnalyzer(analysis_args)
    sa.analyze()

    if analysis_args.show:
        pl.show()
