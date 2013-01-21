from __future__ import division

import numpy as np

from analyze.base import AnalysisCase


class PositionsAnalysis(AnalysisCase):

    def savefile_postfix(self):
        return 'positions'

    def build_axes(self, fig):
        return [fig.add_subplot(111)]

    def analyze_inner(self, axs):
        print 'Analyzing positions'

        positions = np.array([s.idx / (s.qt_length - 1) for s in self.data])

        axs[0].hist(positions, 10, normed=True, label=self.aa.ingraph_text)
        axs[0].set_xlabel('Normalized position')
        axs[0].set_ylabel('Probability density')
        axs[0].legend(loc='best')

    def print_fig_text(self, fig, title):
        fig.text(0.5, 0.95,
                 self.latexize(title + ' --- positions'),
                 ha='center')
