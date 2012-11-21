import pylab as pl

class AnalysisCase(object):

    def __init__(self, data):
        self.data = data
        self.fig = pl.figure()

    def analyze(self):
        raise NotImplementedError
