#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for analyzing the position of the substituted word in its sentence.

This analysis produces a probability density of where subsituted words appear
in the sentence (beginning, middle, end, etc.).

"""


from __future__ import division

import numpy as np

from analyze.base import AnalysisCase


class PositionsAnalysis(AnalysisCase):

    """Analyze where the substituted words are positioned in their sentence."""

    def savefile_postfix(self):
        """Get the postfix to add to save file name."""

        return 'positions'

    def build_axes(self, fig):
        """Build the list of axes in `fig` on which to plot the analysis
        (only one set of axes in this case)."""

        return [fig.add_subplot(111)]

    def analyze_inner(self, axs):
        """Perform the analysis in itself, plotting the results on `axs`."""

        print 'Analyzing positions'

        positions = np.array([s.idx / (s.qt_length - 1) for s in self.data])

        axs[0].hist(positions, 10, normed=True, label=self.aa.ingraph_text)
        axs[0].set_xlabel('Normalized position')
        axs[0].set_ylabel('Probability density')
        axs[0].legend(loc='best')

    def print_fig_text(self, fig, title):
        """Print `title` on `fig` with some additional analysis information."""

        fig.text(0.5, 0.95,
                 self.latexize(title + ' --- positions'),
                 ha='center')
