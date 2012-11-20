#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Visualize data from the MemeTracker dataset

Methods:
  * mean_smooth: compute a moving average of a histogram (used in
                 'plot_timeline')
  * dt_toordinal: convert a datetime object to an ordinal, as used by
                  Matplotlib
  * fft_smooth: smooth a histogram by taking the first few Fourier frequencies
  * spline_fft_smooth: smooth a histogram by FFT then splining
  * timestamps_todt: convert a list of timestamps to a list of datetime object

Classes:
  * TimelineVisualize: visualizing methods for Timeline
  * QuoteVisualize: visualizing methods for Quote
  * ClusterVisualize: visualizing methods for Cluster
  * ordTimeDelta: subclass of timedelta that defines the 'toordinal' method,
                  for use in Matplotlib

"""


from __future__ import division

from datetime import datetime, timedelta
from operator import attrgetter
import textwrap

import numpy as np
import pylab as pl
from scipy.interpolate import spline
import matplotlib.dates as md
import matplotlib.cm as cm

import datastructure.base as ds_mtb
import visualize.annotations as v_an


def mean_smooth(x_secs, ipd, smooth_res):
    """Compute a moving average of a histogram (used in plot_timeline).

    Arguments:
      * x_secs: the x values of the histogram (i.e. the middles of the bins)
      * ipd: the histogram values to be smoothed (ipd stands for instances
             per day)
      * smooth_res: the width, in days, of the moving average to be computed

    Returns: a tuple (x_secs_smooth, ipd_smooth) containing the x and y values
             for the computed moving average.

    """

    start = int(pl.ceil(smooth_res / 2))
    end = len(x_secs) - start + 1
    length = end - start

    x_secs_smooth = x_secs[start:end]
    ipd_smooth = pl.mean([ipd[i:length + i] for i in range(smooth_res)], 0)

    return (x_secs_smooth, ipd_smooth)


def fft_smooth(n, n_freqs=7):
    """Smooth a histogram by taking the first few Fourier frequencies.

    Arguments:
      * n: the values of the histogram to smooth

    Keyword arguments:
      * n_freqs: the number of positive and negative frequencies to include.
                 The total number of frequencies kept is 2 * n_freqs + 1.
                 Defaults to 7.

    Returns:
      * out: the smoothed values of the histogram

    """

    nn = pl.concatenate((5 * [n[0]], n, 5 * [n[-1]]))
    l = len(n)
    ll = len(nn)
    ff = np.fft.fft(nn)
    out = np.real(np.array([np.sum([ff[k] * np.exp(2 * np.pi * 1j * m * k /
                                                   ll)
                                    for k in range(- n_freqs, n_freqs + 1)]) /
                            ll for m in range(ll)]))[5:-5]
    out = max(n) * out / max(out)
    return np.max([out, np.zeros(l)], 0)


def spline_fft_smooth(x, n, xnew, n_freqs=7):
    """Smooth a histogram by FFT then splining.

    Arguments:
      * x: the x values of the histogram to smooth
      * n: the values of the histogram to smooth
      * xnew: the new x values for the smoothed data

    Keyword arguments:
      * n_freqs: the number of positive and negative frequencies to include.
                 The total number of frequencies kept is 2 * n_freqs + 1.
                 Defaults to 7.

    Returns:
      * out: the smoothed values of the histogram

    """

    ff = fft_smooth(n, n_freqs)
    return spline(x, ff, xnew)


class ordTimeDelta(timedelta):

    """Subclass of timedelta that defines the 'toordinal' method, for use in
    Matplotlib.

    Methods:
      * toordinal: return the ordinal representation of the TimeDelta object

    """

    def toordinal(self):
        """Return the ordinal representation of the TimeDelta object."""
        return self.days + self.seconds / 86400

    def __truediv__(self, y):
        """Make sure division is done even when __future__.division is on."""
        return self.__div__(y)


def dt_toordinal(dt):
    """Convert a datetime object to an ordinal, as used by Matplotlib."""
    return (dt.toordinal() + dt.hour / 24 + dt.minute / 1440 +
            dt.second / 86400)


def timestamps_todt(timestamps):
    """Convert a list of timestamps to a list of datetime object."""
    return [datetime.utcfromtimestamp(t) for t in timestamps]


class TimelineVisualize(ds_mtb.TimelineBase):

    def plot(self, label='raw timeline, no info', smooth_res=5,
             legend_on=True, legend_size=10.0):
        """Plot the evolution of a Timeline, with an optional legend and an
        optional moving average.

        Optional arguments:
        * label: a legend label; defaults to 'raw timeline, no info'
        * smooth_res: the width, in days, of the moving average; if -1 is given,
                        no moving average is plotted. Defaults to 5 days.
        * legend_on: boolean specifying if the legend is to be shown or not.
                    Defaults to True.
        * legend_size: float specifying the font size of the legend. Defaults
                        to 10.0.

        """

        self.compute_attrs()

        # Convert the epoch-timestamps to dates.

        x_dates = []

        for d in self.ipd_x_secs:
            x_dates.append(datetime.fromtimestamp(d))

        # 'ipd' stands for Instances per Day.

        pl.plot_date(x_dates, self.ipd, xdate=True, fmt='-',
                    label='{} (ipd)'.format(label))

        # Show a smoothed curve if there's enough data, and if we weren't asked
        # not to.

        if smooth_res != -1 and self.span_days > smooth_res:

            x_secs_smooth, ipd_smooth = mean_smooth(self.ipd_x_secs,
                                                    self.ipd, smooth_res)
            x_dates_smooth = []

            for d in x_secs_smooth:
                x_dates_smooth.append(datetime.fromtimestamp(d))

            pl.plot_date(x_dates_smooth, ipd_smooth, xdate=True, fmt='-',
                        label='{} ({}-day moving average)'.format(label,
                                                                smooth_res))

        if legend_on:
            pl.legend(loc='best', prop={'size': legend_size})

    def barflow(self, bins=25):
        """Plot the bar-chart of a Timeline.

        Optional arguments:
        * bins: same argument as the pylab.histogram function (either a integer
                or an array specifying the bin limits). Defaults to 25.

        Returns: the bin limits as returned by pylab.histogram.

        """

        fig = pl.gcf()
        ax = pl.gca()

        # Get the histogram data, and convert the bins to datetime formats.

        heights, bins = pl.histogram(self.url_times, bins=bins)
        widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                    i in range(len(heights))]
        bins_d = timestamps_todt(bins)
        middles = (bins[:-1] + bins[1:]) / 2
        middles_d = timestamps_todt(middles)
        heights_sm = fft_smooth(heights)

        # Plot the bars.

        ax.bar(bins_d[:-1], heights, widths_d, color='cyan')
        ax.set_xlim(min(bins_d), max(bins_d))
        ymax = max(pl.concatenate((heights_sm, heights)))
        ax.set_ylim(-0.1 * ymax, 1.1 * ymax)
        ax.plot(middles_d, heights_sm, lw=2, color='magenta')
        ax.fill_between(middles_d, 0, heights_sm, color='magenta', alpha=0.3,
                        zorder=100)

        # Format the date on the x axis and the coordinate box.

        loc = md.AutoDateLocator()
        formatter = md.AutoDateFormatter(loc)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
        fig.autofmt_xdate()

        return bins


class QuoteVisualize(ds_mtb.QuoteBase,TimelineVisualize):

    def plot(self, smooth_res=5):
        """Plot the time evolution of the Quote (with a legend).

        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution can
                        be additionally plotted; this is the width, in days,
                        of that moving average. If -1 is given, no moving
                        average is plotted. Defaults to 5 days.

        """

        super(QuoteVisualize, self).plot(label=self.__unicode__(),
                                         smooth_res=smooth_res)


class ClusterVisualize(ds_mtb.ClusterBase):

    def plot_quotes(self, smooth_res=-1):
        """Plot the individual Quotes of the Cluster.

        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution of
                        the quotes can be additionally plotted; this is the
                        width, in days, of that moving average. If -1 is
                        given, no moving average is plotted. Defaults to -1
                        (no moving average plotted).

        """

        for qt in self.quotes.values():
            qt.plot(smooth_res=smooth_res)

        pl.title(self.__unicode__())

    def plot(self, smooth_res=5):
        """Plot the time evolution of the Cluster as a single Timeline.

        Optional arguments:
          * smooth_res: when plotting, a moving average of the evolution can
                        be additionally plotted; this is the width, in days,
                        of that moving average. If -1 is given, no moving
                        average is plotted. Defaults to 5 days.

        """

        self.build_timeline()
        self.timeline.plot(label=self.__unicode__(), smooth_res=smooth_res)

    def barflow(self, bins=25):
        """Plot the bar-chart of the Cluster Timeline."""
        self.build_timeline()
        return self.timeline.barflow(bins)

    def bar_quotes(self, bins=25, drawtext=True):
        """Plot the stacked bar-chart of Quotes in a Cluster, with added
        annotations.

        Optional arguments:
        * bins: same argument as the pylab.histogram function (either a integer
                or an array specifying the bin limits). Defaults to 25.
        * drawtext: boolean specifying if text should be displayed for the
                    annotations

        Returns: a tuple consisting of the bins returned by pylab.histogram on the
                Cluster's full Timeline, and of the AnnoteFinderBar object linked
                to the plot.

        """

        fig = pl.gcf()
        ax = pl.gca()

        # Get the bins, to be given as common argument for all Quotes, later on.

        self.build_timeline()
        cl_heights, bins = pl.histogram(self.timeline.url_times, bins=bins)

        nbins = len(bins) - 1
        widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                    i in range(nbins)]
        bins_d = timestamps_todt(bins)

        # For future use in plotting and with the annotations.

        bottoms = np.zeros(nbins)
        l_bottoms = []
        l_heights = []
        l_quotes = sorted(self.quotes.itervalues(), key=attrgetter('tot_freq'),
                        reverse=True)

        # Do the Quote plotting.

        for i, qt in enumerate(l_quotes):

            heights = pl.histogram(qt.url_times, bins=bins)[0]
            ax.bar(left=bins_d[:-1], height=heights, width=widths_d,
                bottom=bottoms, color=cm.YlOrBr(i / self.n_quotes))
            l_bottoms.append(bottoms.copy())
            l_heights.append(heights.copy())
            bottoms += heights

        ax.set_xlim(min(bins_d), max(bins_d))
        ymax = max(cl_heights)
        ax.set_ylim(-0.1 * ymax, 1.1 * ymax)

        # Format the date on the x axis and the coordinate box.

        loc = md.AutoDateLocator()
        formatter = md.AutoDateFormatter(loc)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
        fig.autofmt_xdate()

        # Create and link the annotations.

        af = v_an.AnnoteFinderBar(l_heights,
                                [[dt_toordinal(binlim)
                                    for binlim in bins_d]] * self.n_quotes,
                                l_bottoms, l_quotes, drawtext=drawtext)
        pl.connect('button_press_event', af)

        return (bins, af)

    def flow_quotes(self, bins=25, drawtext=True):
        """Plot the flow of the stacked bar-chart of Quotes in a Cluster, with
        added annotations.

        Optional arguments:
        * bins: same argument as the pylab.histogram function (either a integer
                or an array specifying the bin limits). Defaults to 25.
        * drawtext: boolean specifying if text should be displayed for the
                    annotations

        Returns: a tuple consisting of the bins returned by pylab.histogram on the
                Cluster's full Timeline, and of the AnnoteFinderFlow object
                linked to the plot.

        """

        fig = pl.gcf()
        ax = pl.gca()

        # Get the bins, to be given as common argument for all Quotes, later on.

        self.build_timeline()
        bins = pl.histogram(self.timeline.url_times, bins=bins)[1]

        nbins = len(bins) - 1
        bins_d = timestamps_todt(bins)
        middles = (bins[:-1] + bins[1:]) / 2
        middles_d = timestamps_todt(middles)

        # For future use in plotting and with the annotations.

        bottoms_sm = np.zeros(nbins)
        l_bottoms_sm = []
        l_heights_sm = []
        l_quotes = sorted(self.quotes.itervalues(), key=attrgetter('tot_freq'),
                        reverse=True)

        # Do the Quote plotting.

        ax.plot(middles_d, bottoms_sm, 'k')

        for i, qt in enumerate(l_quotes):

            heights_sm = fft_smooth(pl.histogram(qt.url_times, bins=bins)[0])
            ax.plot(middles_d, heights_sm + bottoms_sm, 'k')
            ax.fill_between(middles_d, bottoms_sm, heights_sm + bottoms_sm,
                            color=cm.YlOrBr(i / self.n_quotes, alpha=1.0))
            l_bottoms_sm.append(bottoms_sm.copy())
            l_heights_sm.append(heights_sm.copy())
            bottoms_sm += heights_sm

        ax.set_xlim(min(bins_d), max(bins_d))
        ymax = max(bottoms_sm)
        ax.set_ylim(-0.1 * ymax, 1.1 * ymax)

        # Format the date on the x axis and the coordinate box.

        loc = md.AutoDateLocator()
        formatter = md.AutoDateFormatter(loc)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
        fig.autofmt_xdate()

        # Create and link the annotations.

        af = v_an.AnnoteFinderFlow([[dt_toordinal(m)
                                    for m in middles_d]] * self.n_quotes,
                                l_bottoms_sm, l_heights_sm, l_quotes,
                                drawtext=drawtext)
        pl.connect('button_press_event', af)

        return (bins, af)

    def bar_quotes_norm(self, bins=25, drawtext=True):
        """Plot the normalized stacked bar-chart of Quotes in a Cluster, with
        added text-less annotations.

        Optional arguments:
        * bins: same argument as the pylab.histogram function (either a integer
                or an array specifying the bin limits). Defaults to 25.
        * drawtext: boolean specifying if text should be displayed for the
                    annotations

        Returns: a tuple consisting of the bins returned by pylab.histogram on the
                Cluster's full Timeline, and of the AnnoteFinderBar object linked
                to the plot. The annotations linked to the plot display no text,
                and will only highlight the bars corresponding to the selected
                Quote. This is meant to be linked to the AnnoteFinderBar object
                returned by bar_cluster, to have those two subplots linked
                together in the same figure.

        """

        fig = pl.gcf()
        ax = pl.gca()

        # Get the bins, to be given as common argument for all Quotes, later on.

        self.build_timeline()
        cl_heights, bins = pl.histogram(self.timeline.url_times, bins=bins)

        nbins = len(bins) - 1
        widths_d = [ordTimeDelta(seconds=bins[i + 1] - bins[i]) for
                    i in range(nbins)]
        bins_d = timestamps_todt(bins)
        middles = (bins[:-1] + bins[1:]) / 2
        middles_d = timestamps_todt(middles)

        # For future use in plotting, normalizing, and annotating.

        bottoms = np.zeros(nbins)
        bottoms_sm = np.zeros(nbins)
        l_bottoms = []
        heights_qt = np.zeros((nbins, self.n_quotes))
        heights_qt_sm = np.zeros((nbins, self.n_quotes))
        l_quotes = sorted(self.quotes.itervalues(), key=attrgetter('tot_freq'),
                        reverse=True)

        # Get the histogram data.

        for i, qt in enumerate(l_quotes):
            heights_qt[:, i] = pl.histogram(qt.url_times, bins=bins)[0]
            heights_qt_sm[:, i] = spline_fft_smooth(middles, heights_qt[:, i],
                                                    middles)

        cl_heights_sm = heights_qt_sm.sum(1)

        # Normalize all the heights to one.

        for j in range(nbins):

            if cl_heights[j] != 0:
                heights_qt[j, :] = heights_qt[j, :] / cl_heights[j]

            if cl_heights_sm[j] != 0:
                heights_qt_sm[j, :] = heights_qt_sm[j, :] / cl_heights_sm[j]

        # Plot the normalized histograms.

        for i in range(self.n_quotes):

            ax.bar(left=bins_d[:-1], height=heights_qt[:, i], width=widths_d,
                bottom=bottoms, color=cm.YlOrBr(i / self.n_quotes))
            ax.plot(middles_d, heights_qt_sm[:, i] + bottoms_sm,
                    color=cm.winter(i / self.n_quotes), lw=2)
            l_bottoms.append(bottoms.copy())
            bottoms += heights_qt[:, i]
            bottoms_sm += heights_qt_sm[:, i]

        ax.set_xlim(min(bins_d), max(bins_d))
        ax.set_ylim(-0.1, 1.1)

        # Format the date on the x axis and the coordinate box.

        loc = md.AutoDateLocator()
        formatter = md.AutoDateFormatter(loc)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.format_xdata = md.DateFormatter('%Y-%m-%d %H:%m:%S')
        fig.autofmt_xdate()

        # Create and link the annotations.

        af = v_an.AnnoteFinderBar(heights_qt.transpose(),
                                [[dt_toordinal(binlim)
                                    for binlim in bins_d]] * self.n_quotes,
                                l_bottoms, l_quotes, drawtext=drawtext)
        pl.connect('button_press_event', af)

        return (bins, af)

    def barflow_all(self, bins=25):
        """Plot the bar-plot, stacked bar-plot, and flow of the stacked bar-
        plot for the cluster, with annotations."""
        pl.subplot(311)
        pl.title(textwrap.fill('{}'.format(self), 70))
        self.barflow(bins)
        pl.subplot(312)
        af1 = self.bar_quotes(bins, drawtext=False)[1]
        pl.subplot(313)
        af2 = self.flow_quotes(bins)[1]
        v_an.linkAnnotationFinders([af1, af2])

