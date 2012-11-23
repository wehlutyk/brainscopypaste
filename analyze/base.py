from warnings import warn
import re

import pylab as pl

from datainterface.fs import check_file, get_fileprefix
import settings as st


class AnalysisCase(object):

    def __init__(self, aa, data):
        self.aa = aa
        self.data = data
        self.fig = pl.figure()
        self.savefile_prefix = get_fileprefix(aa)
        filename = (self.savefile_prefix +
                    re.sub(' ', '-', self.savefile_postfix()))
        self.filepath = st.mt_analysis_figure_file.format(filename)

    def analyze(self):
        if self.aa.save and not self.checkfile():
            return

        self.analyze_inner()
        if self.aa.save:
            self.fig.canvas.print_figure(self.filepath, dpi=300)

    def analyze_inner(self):
        raise NotImplementedError

    def savefile_postfix(self):
        raise NotImplementedError

    def checkfile(self):
        try:
            check_file(self.filepath)
        except Exception:
            if self.aa.overwrite:
                warn('Overwriting file ' + self.filepath)
                return True
            else:
                warn(self.filepath + ' already exists, skipping it')
                return False

        return True
