from __future__ import division

import numpy as np

from analyze.base import AnalysisCase


class PositionAnalysis(AnalysisCase):

    def analyze(self):
        print 'Analyzing positions'

        positions = np.array([s.idx / (s.qt_length - 1) for s in self.data])

        ax = self.fig.add_subplot(111)
        ax.hist(positions, 20, normed=True)
        ax.set_title(self.aa.title(), fontsize='small')
        ax.set_xlabel('Normalized position')
        ax.set_ylabel('Probability density')
