from __future__ import division

from analyze.base import AnalysisCase


class PositionAnalysis(AnalysisCase):

    def analyze(self):

        positions = [s.idx / (s.qt_length - 1) for s in self.data]
        self.fig.hist(positions, 30, normed=True)
        self.fig.title('Histogram of normalized positions of substitutions')
