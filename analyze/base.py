from __future__ import division

from warnings import warn
import re

from datainterface.fs import check_file


class AnalysisCase(object):

    def __init__(self, aa, data):
        self.aa = aa
        self.data = data

    def analyze(self, axs, filepath):
        if self.aa.save and not self.checkfile(filepath):
            return False

        self.analyze_inner(axs)
        return True

    def build_axes(self):
        raise NotImplementedError

    def analyze_inner(self, axs):
        raise NotImplementedError

    def savefile_postfix(self):
        raise NotImplementedError

    def print_fig_text(self, fig, title):
        raise NotImplementedError

    def checkfile(self, filepath):
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
        latex_text = re.sub('\\|', '$|$', text)
        latex_text = re.sub('_', ' ', latex_text)
        return latex_text
