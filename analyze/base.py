import pylab as pl

import datainterface.picklesaver as ps
from datainterface.fs import get_save_file

class AnalysisCase(object):

    def __init__(self, ma):
        self.ma = ma
        self.filename = get_save_file(ma, readonly=True)
        self.data = ps.load(self.filename)

        self.fig = pl.figure()
