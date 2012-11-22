import pylab as pl

class AnalysisCase(object):

    def __init__(self, aa, data):
        self.aa = aa
        self.data = data
        self.fig = pl.figure()

    def analyze(self):
        raise NotImplementedError
