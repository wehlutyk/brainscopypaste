from warnings import warn

import pylab as pl

from datainterface.fs import check_file, get_fileprefix
import settings as st


class AnalysisCase(object):

    def __init__(self, aa, data):
        self.aa = aa
        self.data = data
        self.fig = pl.figure()
        self.savefile_prefix = get_fileprefix(aa)

    def analyze(self):
        raise NotImplementedError

    def savefile_postfix(self):
        raise NotImplementedError

    def save(self):
        if self.aa.save:
            filename = self.savefile_prefix + self.savefile_postfix()
            filepath = st.mt_analysis_figure_file.format(filename)
            try:
                check_file(filepath)
            except Exception, msg:
                if self.aa.overwrite:
                    warn('Overwriting file ' + filepath)
                else:
                    raise Exception(msg)
            self.fig.canvas.print_figure(filepath, dpi=300)
