#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Add annotations to a plot."""


from __future__ import division

import textwrap
from operator import itemgetter

import pylab as pl
from matplotlib.container import BarContainer
import matplotlib.cm as cm


class AnnoteFinder(object):

    """Display annotations in a Matplotlib plot.

    This class defines a callback for Matplotlib to display an annotation when
    points are clicked on. The point which is closest to the click and within
    `xtol` and `ytol` is identified.

    Register this function like this::

        scatter(xdata, ydata)
        af = AnnoteFinder(xdata, ydata, annotes)
        connect('button_press_event', af)

    Parameters
    ----------
    xdata : list or ndarray
        Data on the x axis.
    ydata : list or ndarray
        Data on the y axis.
    annotes : list of strings
        The annotations corresponding to data points defined by the couples
        in ``zip(xdata, ydata)``.
    axis : :class:`~matplotlib.axes.Axes` instance, optional
        The :class:`~matplotlib.axes.Axes` object to draw on; defaults to
        the current axis (as given by ``gca()``).
    xtol : float, optional
        Tolerance in the x direction for clicking on a point; defaults
        to the mean distance between points on the x axis, divided by two.
    ytol : float, optional
        Tolerance in the y direction for clicking on a point; defaults to
        the mean distance between points on the y axis, divided by two.

    Attributes
    ----------
    data : list of tuples
        Equal to ``zip(xdata, ydata, annotes)``.
    xtol : float
        The x tolerance passed to the contructor.
    ytol : float
        The y tolerance passed to the contructor.
    axis : :class:`~matplotlib.axes.Axes`
        The axes to draw on.

    See Also
    --------
    AnnoteFinderBar, AnnoteFinderFlow, AnnoteFinderPlot

    """

    def __init__(self, xdata, ydata, annotes, axis=None, xtol=None, ytol=None):
        """Initialize the annotator.

        Parameters
        ----------
        xdata : list or ndarray
            Data on the x axis.
        ydata : list or ndarray
            Data on the y axis.
        annotes : list of strings
            The annotations corresponding to data points defined by the couples
            in ``zip(xdata, ydata)``.
        axis : :class:`~matplotlib.axes.AxesSubplot` instance, optional
            The :class:`~matplotlib.axes.AxesSubplot` object to draw on;
            defaults to the current axis (as given by ``gca()``).
        xtol : float, optional
            Tolerance in the x direction for clicking on a point; defaults
            to the mean distance between points on the x axis, divided by two.
        ytol : float, optional
            Tolerance in the y direction for clicking on a point; defaults to
            the mean distance between points on the y axis, divided by two.

        """

        self.data = zip(xdata, ydata, annotes)

        # Set the tolerances.

        if xtol is None:
            xtol = ((max(xdata) - min(xdata)) / float(len(xdata))) / 2
        if ytol is None:
            ytol = ((max(ydata) - min(ydata)) / float(len(ydata))) / 2

        self.xtol = xtol
        self.ytol = ytol

        # Set the axes.

        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis

        # For later use, keeping track of what is drawn and what other plot
        # we're connected to.

        self.drawnAnnotations = {}
        self.links = []
        self.plotlinks = []

    def distance(self, x1, x2, y1, y2):
        """Compute the distance between `(x1, y1)` and `(x2, y2)`."""

        return pl.norm([x1 - x2, y1 - y2])

    def __call__(self, event):
        """The callback called by Matplotlib on a click event (if we connect
        the AnnoteFinder to a click event).

        This function finds the data point nearest to the click point, and
        draws the corresponding annotation in all the connected plots.

        Parameters
        ----------
        event : Matplotlib event
            The event object sent by Matplotlib.

        """

        # Only if we're in the axes, and we're not zooming or in another mode.

        if event.inaxes and pl.get_current_fig_manager().toolbar.mode == '':

            clickX = event.xdata
            clickY = event.ydata

            # Only if we're in our axes.

            if self.axis is None or self.axis == event.inaxes:

                # Get all the annotes fitting the tolerance criterion.

                annotes = []

                for (x, y, a) in self.data:

                    if (clickX - self.xtol < x < clickX + self.xtol and
                            clickY - self.ytol < y < clickY + self.ytol):
                        annotes.append((self.distance(x, clickX, y, clickY),
                                        x, y, a))

                # Then grab the nearest data point and draw on every connected
                # plot.

                if annotes:

                    annotes.sort()
                    x, y, annote = annotes[0][1:]
                    self.drawAnnote(event.inaxes, x, y, annote)

                    for l in self.links:
                        l.drawSpecificAnnote(annote)

    def drawAnnote(self, axis, x, y, annote):
        """Draw an annotation on the plot.

        Parameters
        ----------
        axis : :class:`~matplotlib.axes.Axes`
            The axis to draw on.
        x : float
            The x coordinate of the data point.
        y : float
            The y coordinate of the data point.
        annote : string
            The annotation to draw.

        """

        # If the annotation is already drawn, change its visibility.

        if (x, y) in self.drawnAnnotations:

            markers = self.drawnAnnotations[(x, y)]

            for m in markers:

                hiding = m.get_visible()
                m.set_visible(not m.get_visible())

            if hiding:

                for plotlink in self.plotlinks:
                    plotlink.cla()

            else:

                for plotlink in self.plotlinks:
                    plotlink.drawSpecificAnnote(annote)

            self.axis.figure.canvas.draw()

        # Else create the annotation, store it, and display it.

        else:

            for plotlink in self.plotlinks:
                plotlink.drawSpecificAnnote(annote)

            t = axis.annotate('({}, {})\n{}'.format(x, y, annote),
                              xy=(x, y),
                              xycoords='data',
                              xytext=(0, -100),
                              textcoords='offset points',
                              bbox=dict(boxstyle='round',
                                        fc=(0.95, 0.8, 1.0, 0.8),
                                        ec=(0.85, 0.4, 1.0, 0.8)),
                              arrowprops=dict(arrowstyle='wedge,tail_width=1.',
                                              fc=(0.95, 0.8, 1.0, 0.8),
                                              ec=(0.85, 0.4, 1.0, 0.8),
                                              patchA=None,
                                              patchB=None,
                                              relpos=(0.1, 1.0),
                                              connectionstyle='arc3,rad=0'))
            m = axis.plot([x], [y], marker='o', color='yellow', zorder=100,
                          markersize=10)[0]
            self.drawnAnnotations[(x, y)] = (t, m)
            self.axis.figure.canvas.draw()

    def drawSpecificAnnote(self, annote):
        """Draw all the annotations corresponding to `annote` (misnomer)."""

        annotesToDraw = [(x, y, a) for (x, y, a) in self.data if a == annote]
        for (x, y, a) in annotesToDraw:
            self.drawAnnote(self.axis, x, y, a)


class AnnoteFinderBar(object):

    """Display annotations in a Matplotlib bar-plot.

    This class defines a callback for Matplotlib to display an annotation when
    bars are clicked on. The data set which is closest to the click and within
    `xtol` and `ytol` is identified.

    Register this function like this::

        for i in range(num_data_series):
            bar(l_lefts[i], l_heights[i], l_widths[i], l_bottoms[i])
        af = AnnoteFinder(l_heights, l_lefts + l_widths[-1], l_bottoms,
                          annotes)
        connect('button_press_event', af)

    Parameters
    ----------
    l_heights : list of floats
        A list of heights of the bars in the bar-plot, one for each
        data set.
    l_bins : list of list of bins
        A list of lists of bin limits used in the bar-plots, one for each
        data set.
    l_bottoms : list of floats
        A list of bottoms of the bars in the bar-plot, one for each
        data set.
    annotes : list of objects
        A list of annotations, each one corresponding to a data set; each
        annote object should have an `id` attribute, to be displayed after
        formatting as ``'{}'.format(annote)``.
    axis : :class:`~matplotlib.axes.Axes` instance, optional
        The :class:`~matplotlib.axes.Axes` object to draw on; defaults
        to the current axis (as given by ``gca()``).
    xtol : float, optional
        Tolerance in the x direction for clicking on a point; defaults to
        the minimum width of a bin divided by two.
    ytol : float, optional
        Tolerance in the y direction for clicking on a point; defaults to
        the maximum height of a bar in the bar-plot divided by five.
    drawtext : bool
        Wehter or not the text of the annotes should be shown; if not,
        the bars are only highlighted when clicked on, and no additional
        text is shown; this is meant to be used when linking with another
        bar-plot of the same data, which will show the text (meaning
        there is no need for the text to be shown again in this plot);
        defaults to ``True``.

    Attributes
    ----------
    data : list of tuples
        Equal to ``zip(l_heights, l_bins, l_bottoms, annotes)``.
    xtol : float
        The x tolerance passed to the contructor.
    ytol : float
        The y tolerance passed to the contructor.
    axis : :class:`~matplotlib.axes.Axes`
        The axes to draw on.
    drawtext : bool
        The `drawtext` parameter passed to the constructor.

    See Also
    --------
    AnnoteFinder, AnnoteFinderFlow, AnnoteFinderPlot

    """

    def __init__(self, l_heights, l_bins, l_bottoms, annotes, axis=None,
                 xtol=None, ytol=None, drawtext=True):
        """Initialize the annotator.

        Parameters
        ----------
        l_heights : list of floats
            A list of heights of the bars in the bar-plot, one for each
            data set.
        l_bins : list of list of bins
            A list of lists of bin limits used in the bar-plots, one for each
            data set.
        l_bottoms : list of floats
            A list of bottoms of the bars in the bar-plot, one for each
            data set.
        annotes : list of objects
            A list of annotations, each one corresponding to a data set; each
            annote object should have an `id` attribute, to be displayed after
            formatting as ``'{}'.format(annote)``.
        axis : :class:`~matplotlib.axes.Axes` instance, optional
            The :class:`~matplotlib.axes.Axes` object to draw on; defaults
            to the current axis (as given by ``gca()``).
        xtol : float, optional
            Tolerance in the x direction for clicking on a point; defaults to
            the minimum width of a bin divided by two.
        ytol : float, optional
            Tolerance in the y direction for clicking on a point; defaults to
            the maximum height of a bar in the bar-plot divided by five.
        drawtext : bool
            Wehter or not the text of the annotes should be shown; if not,
            the bars are only highlighted when clicked on, and no additional
            text is shown; this is meant to be used when linking with another
            bar-plot of the same data, which will show the text (meaning
            there is no need for the text to be shown again in this plot);
            defaults to ``True``.

        """

        self.data = zip(l_heights, l_bins, l_bottoms, annotes)
        self.drawtext = drawtext

        # Set the tolerances.

        if xtol is None:
            xtol = min([min(bins) for bins in l_bins]) / 2
        if ytol is None:
            ytol = max([max([t for t in heights + bottoms]) for
                        (heights, bottoms) in zip(l_heights, l_bottoms)]) / 5

        self.xtol = xtol
        self.ytol = ytol

        # Set the axes.

        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis

        # For later use, keeping track of what is drawn and what other plot
        # we're connected to.

        self.drawnAnnotations = {}
        self.links = []

    def distance(self, x1, x2, y1, y2):
        """Compute the distance between `(x1, y1)` and `(x2, y2)`."""

        return pl.norm([x1 - x2, y1 - y2])

    def is_in_bars(self, x, y, heights, bins, bottoms):
        """Detect if a click is within tolerance range of a bar-plot.

        Parameters
        ----------
        x : float
            The x coordinate of the click.
        y : float
            The y coordinate of the click.
        heights : list of floats
            The heights of the bars.
        bins : list of floats
            The bin limits used in plotting the bars.
        bottoms : list of floats
            The bottoms of the bars.

        Returns
        -------
        (is_in_bars, dj) : tuple
            `is_in_bars` is a boolean saying if the click is within tolerance
            of the bar-plot; `dj` is either `None` (if
            ``is_in_bars == False``), or a tuple consisting of the distance
            between the click point and the closest bar, and the x-index of
            that closest bar (if ``is_in_bars == True``).

        """

        is_in_bars = False
        distances = []

        # For each bar...

        for j in range(len(heights)):

            # ... if we're in the tolerance, store the distance to that bar

            if (bins[j] - self.xtol < x < bins[j + 1] + self.xtol and
                    bottoms[j] - self.ytol < y < bottoms[j] +
                    heights[j] + self.ytol):

                is_in_bars = True

                x_dist = max([0, bins[j] - x, x - bins[j + 1]])
                y_dist = max([0, bottoms[j] - y,
                              y - (bottoms[j] + heights[j])])
                distance = pl.norm([x_dist, y_dist])
                distances.append((distance, j))

        # Return the closest bar.

        dj = sorted(distances)[0] if is_in_bars else None
        return (is_in_bars, dj)

    def __call__(self, event):
        """The callback called by Matplotlib on a click event (if we connect
        the :class:`AnnoteFinderBar` to a click event).

        This function finds the data set corresponding to the bars nearest to
        the click point, and draws the corresponding annotation in all the
        connected plots. The drawn annotations consist of a highlighting of
        the bars, and a text (if ``self.drawtext == True``).

        Parameters
        ----------
        event : Matplolib event
            The event object sent by Matplotlib.

        """

        # Only if we're in the axes, and we're not zooming or in another mode.

        if event.inaxes and pl.get_current_fig_manager().toolbar.mode == '':

            clickX = event.xdata
            clickY = event.ydata

            # Only if we're in our axes.

            if self.axis is None or self.axis == event.inaxes:

                # Get all the annotes fitting the tolerance criterion.

                annotes = []

                for (i, (heights, bins, bottoms, a)) in enumerate(self.data):

                    (is_in_bars, dj) = self.is_in_bars(clickX, clickY,
                                                       heights, bins,
                                                       bottoms)

                    if is_in_bars:

                        (d, j) = dj
                        annotes.append((d, i, j, a))

                # Then grab the nearest data point and draw on every connected
                # plot.

                if annotes:

                    (i, j, annote) = sorted(annotes,
                                            key=itemgetter(0))[0][1:]
                    self.drawAnnote(event.inaxes, i, j, clickX, annote)

                    for l in self.links:
                        l.drawAnnote(l.axis, i, j, clickX, annote)

    def drawAnnote(self, axis, i, j, x, annote):
        """Draw an annotation on the plot.

        Parameters
        ----------
        axis : :class:`~matplolib.axes.Axes`
            The axis to draw on.
        i : int
            The index of the data series for which we're to draw the annote.
        j : int
            The x-index of the bar which is to receive the text-anchor.
        x : float
            The x coordinate for the annote - deprecated.
        annote : string
            The annotation to draw; it should have an `id` attribute; the
            text shown will be formatted using ``'{}'.format(annote)``.

        """

        # If the annotation is already drawn, remove it.

        if annote.id in self.drawnAnnotations:

            markers = self.drawnAnnotations.pop(annote.id)

            for m in markers:

                if m:

                    if type(m) == BarContainer:

                        for p in m.patches:
                            p.set_visible(not p.get_visible())

                    else:
                        m.set_visible(not m.get_visible())

            self.axis.figure.canvas.draw()

        # Else create the annotation, store it, and display it.

        else:

            (heights, bins, bottoms) = self.data[i][:3]
            x = (bins[j] + bins[j + 1]) / 2
            y = bottoms[j] + heights[j] / 2

            # Create the text if asked for.

            if self.drawtext:
                t = axis.annotate(
                    textwrap.fill('{}'.format(annote), 70),
                    xy=(x, y), xycoords='data', xytext=(0, 200),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round',
                              fc=(0.95, 0.8, 1.0, 0.8),
                              ec=(0.85, 0.4, 1.0, 0.8)),
                    arrowprops=dict(arrowstyle='wedge,tail_width=1.',
                                    fc=(0.95, 0.8, 1.0, 0.8),
                                    ec=(0.85, 0.4, 1.0, 0.8),
                                    patchA=None,
                                    patchB=None,
                                    relpos=(0.1, 1.0),
                                    connectionstyle='arc3,rad=0'))
            else:
                t = None

            # Shift the color of the bar to highlight it.

            color_o = cm.YlOrBr(i / len(self.data))
            color = (color_o[1], color_o[2], color_o[0], color_o[3])

            widths = [bins[k + 1] - bins[k] for k in range(len(bins) - 1)]
            m = axis.bar(bins[:-1], heights, widths, bottoms,
                         color=color, edgecolor=(0.0, 0.0, 0.0, 0.0))
            self.drawnAnnotations[annote.id] = (t, m)
            self.axis.figure.canvas.draw()


class AnnoteFinderFlow(object):

    """Display annotations in a Matplotlib flow bar-plot.

    This class defines a callback for Matplotlib to display an annotation when
    flows are clicked on. The data set where the click was is identified.

    Register this function like this:

    >>> for i in range(num_data_series):
    >>>     fill_between(l_xs[i], l_bottoms[i], l_heights[i] + l_bottoms[i])
    >>> af = AnnoteFinder(l_xs, l_bottoms, l_heights, annotes)
    >>> connect('button_press_event', af)

    Methods:
      * __init__: initialize the annotator
      * distance: compute the distance between two points
      * is_in_flow: detect if a click is within tolerance range of a flow
      * __call__: the callback called by Matplotlib on a click event (if we
                  connect the AnnoteFinderFlow to a click event)
      * drawAnnote: draw an annotation on the plot

    """

    def __init__(self, l_xs, l_bottoms, l_heights, annotes, axis=None,
                  drawtext=True):
        """Initialize the annotator.

        Arguments:
          * l_xs: a list of x coordinates of the flows, one for each data set
          * l_bottoms: a list of bottoms of the flow in the flow-plot, one for
                       each data set
          * l_heights: a list of heights of the flows in the flow-plot, one
                       for each data set
          * annotes: a list of annotations, each one corresponding to a data
                     set. Each annote object should have an 'id' attribute,
                     will be displayed after formatting as
                     '{}'.format(annote).

        Optional arguments:
          * axis: the matplotlib.axes.AxesSubplot object to draw on. Defaults
                  to the current axis (as given by gca()).
          * drawtext: a boolean specifying if the text of the annotes should
                      be shown of not. If not, the bars are only highlighted
                      when clicked on, and no additional text is shown. This
                      is meant to be used when linking with another bar-plot
                      of the same data, which will show the text (meaning
                      there is no need for the text to be shown again in this
                      plot). Defaults to True.

        """

        self.data = zip(l_xs, l_bottoms, l_heights, annotes)
        self.drawtext = drawtext

        # Set the axes.

        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis

        # For later use, keeping track of what is drawn and what other plot
        # we're connected to.

        self.drawnAnnotations = {}
        self.links = []

    def distance(self, x1, x2, y1, y2):
        """Compute the distance between two points."""
        return pl.norm([x1 - x2, y1 - y2])

    def is_in_flow(self, x, y, xs, bottoms, heights):
        """Detect if a click is within tolerance range of a flow.

        Arguments:
          * x: the x coordinate of the click
          * y: the y coordinate of the click
          * xs: the x coordinates of the flow
          * bottoms: the bottoms of the flow
          * heights: the heights of the flow

        Returns: a tuple consisting of:
          * is_in_flow: a boolean saying if the click is within tolerance of
                        the bar-plot
          * j: the x-index of the closest point in the flow data to the left
               of the click, if is_in_flow == True (None otherwise)

        """

        is_in_flow = False

        for j in range(len(xs) - 1):

            if xs[j] <= x <= xs[j+1]:

                h_interp = (heights[j] +
                            ((heights[j + 1] - heights[j]) /
                             (xs[j + 1] - xs[j])) * (x - xs[j]))
                b_interp = (bottoms[j] +
                            ((bottoms[j + 1] - bottoms[j]) /
                             (xs[j + 1] - xs[j])) * (x - xs[j]))
                if b_interp <= y <= b_interp + h_interp:

                    is_in_flow = True
                    break

        j = j if is_in_flow else None
        return (is_in_flow, j)

    def __call__(self, event):
        """The callback called by Matplotlib on a click event (if we connect
        the AnnoteFinderFlow to a click event).

        Arguments:
          * event: the event object sent by Matplotlib

        This function finds the data set corresponding to the bars nearest to
        the click point, and draws the corresponding annotation in all the
        connected plots. The drawn annotations consist of a highlighting of
        the flow, and a text (if self.drawtext == True).

        """

        # Only if we're in the axes, and we're not zooming or in another mode.

        if event.inaxes and pl.get_current_fig_manager().toolbar.mode == '':

            clickX = event.xdata
            clickY = event.ydata

            # Only if we're in our axes.

            if self.axis is None or self.axis == event.inaxes:

                # Get the annote in the flow, if it exists.

                annote = None

                for (i, (xs, bottoms, heights, a)) in enumerate(self.data):

                    (is_in_flow, j) = self.is_in_flow(clickX, clickY, xs,
                                                      bottoms, heights)

                    if is_in_flow:

                        annote = a
                        break

                # Then plot it.

                if annote:

                    self.drawAnnote(event.inaxes, i, j, clickX, annote)

                    for l in self.links:
                        l.drawAnnote(l.axis, i, j, clickX, annote)

    def drawAnnote(self, axis, i, j, x, annote):
        """Draw an annotation on the plot.

        Arguments:
          * axis: the axis to draw on
          * i: the index of the data series for which we're to draw the annote
          * j: the x index of the closest point in the flow data to the left
               of x (see next argument).
          * x: the x-coordinate for the annote to draw
          * annote: the annotation to draw. It should have an 'id' attribute.
                    The text shown will be formatted using
                    '{}'.format(annote).

        """

        # If the annotation is already drawn, remove it.

        if annote.id in self.drawnAnnotations:

            markers = self.drawnAnnotations.pop(annote.id)

            for m in markers:

                if m:
                    m.set_visible(not m.get_visible())

            self.axis.figure.canvas.draw()

        # Else create the annotation, store it, and display it.

        else:

            (xs, bottoms, heights) = self.data[i][:3]

            # If j is out of bounds (meaning it probably comes from a linked
            # AnnoteFinderBar object, where j can be 1 + the max here), set it to
            # the max.

            if j >= len(xs) - 1:
                j = len(xs) - 2

            h_interp = (heights[j] +
                        ((heights[j + 1] - heights[j]) /
                         (xs[j + 1] - xs[j])) * (x - xs[j]))
            b_interp = (bottoms[j] +
                        ((bottoms[j + 1] - bottoms[j]) /
                         (xs[j + 1] - xs[j])) * (x - xs[j]))
            y = b_interp + h_interp / 2

            # Create the text if asked for.

            if self.drawtext:
                t = axis.annotate(textwrap.fill('{}'.format(annote), 70),
                                  xy=(x, y),
                                  xycoords='data',
                                  xytext=(0, 200),
                                  textcoords='offset points',
                                  bbox=dict(boxstyle='round',
                                            fc=(0.95, 0.8, 1.0, 0.8),
                                            ec=(0.85, 0.4, 1.0, 0.8)),
                                  arrowprops=
                                      dict(arrowstyle='wedge,tail_width=1.',
                                           fc=(0.95, 0.8, 1.0, 0.8),
                                           ec=(0.85, 0.4, 1.0, 0.8),
                                           patchA=None,
                                           patchB=None,
                                           relpos=(0.1, 1.0),
                                           connectionstyle='arc3,rad=0'))
            else:
                t = None

            # Shift the color of the flow to highlight it.

            color_o = cm.YlOrBr(i / len(self.data))
            color = (color_o[1], color_o[2], color_o[0], color_o[3])

            m = axis.fill_between(xs, bottoms, heights + bottoms, color=color,
                                  edgecolor=(0.0, 0.0, 0.0, 0.0))
            self.drawnAnnotations[annote.id] = (t, m)
            self.axis.figure.canvas.draw()


def linkAnnotationFinders(afs):
    """Link a list of AnnoteFinder|AnnoteFinderBar objects together."""
    for i in range(len(afs)):

        allButSelfAfs = afs[:i] + afs[i + 1:]
        afs[i].links.extend(allButSelfAfs)


class AnnoteFinderPlot(object):

    """Display a plot when clicking a data point in another Matplotlib plot.

    This class defines drawSpecificAnnote function, to be called by other
    AnnoteFinders when clicked on.

    Register this function like this:

    >>> scatter(xdata, ydata)
    >>> af = AnnoteFinder(xdata, ydata, annotes)
    >>> connect('button_press_event', af)
    >>> af2 = AnnoteFinderPlot(second_annotes, second_fig, second_axis,
                               second_plot)
    >>> af.links.append(af2)

    Methods:
      * __init__: initialize the annotator
      * drawSpecificAnnote: draw a plot, corresponding to an annote from
                            another AnnoteFinder
      * cla: clear the axes

    """

    def __init__(self, annotes, second_fig, second_axis, second_plot,
                  axis=None, xtol=None, ytol=None):
        """Initialize the annotator.

        Arguments:
          * annotes: a dict of parameters; keys are (x, y) tuples, and values
                     are parameters passed to the second_plot function
          * second_axis: the axes where the auxiliary plotting is to be done
          * second_plot: the plotting function for the auxiliary axis

        """

        self.annotes = annotes

        # Set the axes.

        self.second_fig = second_fig
        self.second_axis = second_axis
        self.second_plot = second_plot

    def drawSpecificAnnote(self, annote):
        """Draw a plot, corresponding to an annote from another
        AnnoteFinder."""
        self.second_plot(self.second_axis, self.annotes[annote])
        self.second_fig.canvas.draw()

    def cla(self):
        """Clear the axes."""
        if type(self.second_axis) == list:
            for ax in self.second_axis:
                ax.cla()
        else:
            self.second_axis.cla()
