#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base analysis objects upon which analysis classes build.

See example usages in :mod:`.features`, :mod:`.paths`, and :mod:`.positions`.

"""


from __future__ import division

from warnings import warn
import re

from datainterface.fs import check_file


class AnalysisCase(object):

    """Base analysis class on which you build an analysis case.

    This class defines the interface that an analysis case should implement,
    interface which is later used in :mod:`.substitutions`.

    Parameters
    ----------
    aa : :class:`AnalysisArgs` instance
        Arguments for the analysis to be run.
    data : list
        The data to be analyzed by the `analyze` and `analyze_inner` methods,
        usually a list of :class:`mine.substitutions.Substitution`'s.

    Attributes
    ----------
    aa : :class:`AnalysisArgs` instance
        The arguments passed to the constructor.
    data : list
        The data to be analyzed by the `analyze` and `analyze_inner` methods, \
        usually a list of :class:`mine.substitutions.Substitution`'s.

    See Also
    --------
    .args.AnalysisArgs, .features.FeatureAnalysis,
    .paths.PathsAnalysis, .positions.PositionsAnalysis

    """

    def __init__(self, aa, data):
        """Initialize the structure with analysis arguments and analysis data.

        Parameters
        ----------
        aa : :class:`AnalysisArgs` instance
            Arguments for the analysis to be run.
        data : list
            The data to be analyzed by the `analyze` and `analyze_inner`
            methods, usually a list of
            :class:`mine.substitutions.Substitution`'s.

        """

        self.aa = aa
        self.data = data

    def analyze(self, axs, filepath):
        """Check for the existence of our target saving file, and run our
        analysis.

        If the target file already exists and `self.aa.save` is ``True``
        (meaning the final figure should be saved), and `self.aa.overwrite`
        is not, the analysis is aborted to not overwrite an existing figure.

        Parameters
        ----------
        axs : list of :class:`matplotlib.axes.Axes` instance
            The list of axes on which to plot the analysis.
        filepath : string
            The filepath to which the figure is saved if `self.aa.save`
            is ``True``.

        Returns
        -------
        bool
            ``True`` if the analysis was performed, ``False`` if it was aborted
            because of file existence.

        See Also
        --------
        analyze_inner

        """

        if self.aa.save and not self.checkfile(filepath):
            return False

        self.analyze_inner(axs)
        return True

    def build_axes(self):
        """Return the (created) list of :class:`matplotlib.axes.Axes` on which
        to plot the analysis (abstract method)."""

        raise NotImplementedError

    def analyze_inner(self, axs):
        """Perform the analysis and plotting itself (abstract method).

        Parameters
        ----------
        axs : list of :class:`matplotlib.axes.Axes` instance
            The list of axes on which to plot the analysis.

        """

        raise NotImplementedError

    def savefile_postfix(self):
        """Return the filename postfix, used to create the save file
        (abstract method)."""

        raise NotImplementedError

    def print_fig_text(self, fig, title):
        """Print the `title` text on figure `fig`, possibly with additional
        information (abstract method)."""

        raise NotImplementedError

    def checkfile(self, filepath):
        """Check for existence of `filepath` and report depending on our
        saving arguments.

        Parameters
        ----------
        filepath : string
            The file path to check for.

        Returns
        -------
        bool
            ``True`` if the analysis can take place (i.e. if either `filepath`
            does not exist, or it does but `self.aa.overwrite` is ``True``),
            ``False`` otherwise.

        """

        try:
            check_file(filepath)
        except Exception:
            if self.aa.overwrite:
                warn('Overwriting file ' + filepath)
                return True
            else:
                warn(filepath + ' already exists, skipping it')
                return False

        return True

    @classmethod
    def latexize(cls, text):
        """Convert `text` (to be printed on a figure) to a more latex-friendly
        format.

        Returns
        -------
        string
            The converted text.

        """

        latex_text = re.sub('\\|', '$|$', text)
        latex_text = re.sub('_', ' ', latex_text)
        return latex_text
