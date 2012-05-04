#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Add annotations to a plot.

Classes:
  * AnnoteFinder: display annotations in a Matplotlib plot
  * AnnoteFinderBar: display annotations in a Matplotlib bar-plot

Methods:
  * linkAnnotationFinders: link a list of AnnoteFinder|AnnoteFinderBar objects
                           together

"""


from __future__ import division

import textwrap
from operator import itemgetter

import pylab as pl
from numpy import random
from matplotlib.container import BarContainer
import matplotlib.cm as cm


class AnnoteFinder(object):
    
    """Display annotations in a Matplotlib plot.
    
    This class defines a callback for Matplotlib to display an annotation when
    points are clicked on. The point which is closest to the click and within
    xtol and ytol is identified.
      
    Register this function like this:
      
    >>> scatter(xdata, ydata)
    >>> af = AnnoteFinder(xdata, ydata, annotes)
    >>> connect('button_press_event', af)
    
    Methods:
      * __init__: initialize the annotator
      * distance: compute the distance between two points
      * __call__: the callback called by Matplotlib on a click event (if we
                  connect the AnnoteFinder to a click event)
      * drawAnnote: draw an annotation on the plot
      * drawSpecificAnnote: draw all the annotations corresponding to 'annote'
    
    """
    
    def __init__(self, xdata, ydata, annotes, axis=None,
                  xtol=None, ytol=None):
        """Initialize the annotator.
        
        Arguments:
          * xdata: data on the x axis
          * ydata: data on the y axis
          * annotes: the annotations corresponding to data points defined by
                     the couple in zip(xdata, ydata)
        
        Optional arguments:
          * axis: the matplotlib.axes.AxesSubplot object to draw on. Defaults
                  to the current axis (as given by gca()).
          * xtol: tolerance in the x direction for clicking on a point.
                  Defaults to the mean distance between points on the x axis,
                  divided by two.
          * ytol: tolerance in the y direction for clicking on a point.
                  Defaults to the mean distance between points on the y axis,
                  divided by two.
        
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
    
    def distance(self, x1, x2, y1, y2):
        """Compute the distance between two points."""
        return pl.norm(x1 - x2, y1 - y2)
    
    def __call__(self, event):
        """The callback called by Matplotlib on a click event (if we connect
        the AnnoteFinder to a click event).
        
        Arguments:
          * event: the event object sent by Matplotlib
        
        This function finds the data point nearest to the click point, and
        draws the corresponding annotation in all the connected plots.
        
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
        
        Arguments:
          * axis: the axis to draw on
          * x: the x coordinate of the data point
          * y: the y coordinate of the data point
          * annote: the annotation to draw
        
        """
        
        # If the annotation is already drawn, change its visibility.
        
        if (x, y) in self.drawnAnnotations:
            
            markers = self.drawnAnnotations[(x, y)]
            
            for m in markers:
                m.set_visible(not m.get_visible())
            
            self.axis.figure.canvas.draw()
        
        # Else create the annotation, store it, and display it.
        
        else:
            
            t = axis.annotate('({}, {})\n{}'.format(x, y ,annote),
                              xy=(x, y),
                              xycoords='data',
                              xytext=(0, -200),
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
            m = axis.scatter([x], [y], marker='d', c='r', zorder=100)
            self.drawnAnnotations[(x, y)] = (t, m)
            self.axis.figure.canvas.draw()
    
    def drawSpecificAnnote(self, annote):
        """Draw all the annotations corresponding to 'annote'."""
        annotesToDraw = [(x, y, a) for (x, y, a) in self.data if a == annote]
        for (x, y, a) in annotesToDraw:
            self.drawAnnote(self.axis, x, y, a)


class AnnoteFinderBar(object):
    
    """Display annotations in a Matplotlib bar-plot.
    
    This class defines a callback for Matplotlib to display an annotation when
    bars are clicked on. The data set which is closest to the click and within
    xtol and ytol is identified.
      
    Register this function like this:
      
    >>> for i in range(num_data_series):
    >>>     bar(l_lefts[i], l_heights[i], l_widths[i], l_bottoms[i])
    >>> af = AnnoteFinder(l_heights, l_lefts + l_widths[-1], l_bottoms,
                          annotes)
    >>> connect('button_press_event', af)
    
    Methods:
      * __init__: initialize the annotator
      * distance: compute the distance between two points
      * is_in_bars: detect if a click is within tolerance range of a bar-plot
      * __call__: the callback called by Matplotlib on a click event (if we
                  connect the AnnoteFinderBar to a click event)
      * drawAnnote: draw an annotation on the plot
    
    """
    
    def __init__(self, l_heights, l_bins, l_bottoms, annotes, axis=None,
                  xtol=None, ytol=None, drawtext=True):
        """Initialize the annotator.
        
        Arguments:
          * l_heights: a list of heights of the bars in the bar-plot, one for
                       each data set
          * l_bins: a list of bins used in the bar-plots, one for each data
                    set
          * l_bottoms: a list of bottoms of the bars in the bar-plot, one for
                       each data set
          * annotes: a list of annotations, each one corresponding to a data
                     set. each annote object should have an 'id' attribute,
                     will be displayed after formatting as
                     '{}'.format(annote).
        
        Optional arguments:
          * axis: the matplotlib.axes.AxesSubplot object to draw on. Defaults
                  to the current axis (as given by gca()).
          * xtol: tolerance in the x direction for clicking on a point.
                  Defaults to the minimum width of a bin divided by two.
          * ytol: tolerance in the y direction for clicking on a point.
                  Defaults to the maximum height of a bar in the bar-plot
                  divided by five.
          * drawtext: a boolean specifying if the text of the annotes should
                      be shown of not. If not, the bars are only highlighted
                      when clicked on, and no additional text is shown. This
                      is meant to be used when linking with another bar-plot
                      of the same data, which will show the text (meaning
                      there is no need for the text to be shown again in this
                      plot). Defaults to True.
        
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
        """Compute the distance between two points."""
        return pl.norm([x1 - x2, y1 - y2])
    
    def is_in_bars(self, x, y, heights, bins, bottoms):
        """Detect if a click is within tolerance range of a bar-plot.
        
        Arguments:
          * x: the x coordinate of the click
          * y: the y coordinate of the click
          * heights: the heights of the bars
          * bins: the bins used in plotting the bars
          * bottoms: the bottoms of the bars
        
        Returns: a tuple consisting of:
          * is_in_bars: a boolean saying if the click is within tolerance of
                        the bar-plot
          * dj: either None (if is_in_bars == False), or a tuple consisting
                of the distance between the click point and the closest bar,
                and the x-index of that closest bar (if is_in_bars == True)
        
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
        the AnnoteFinderBar to a click event).
        
        Arguments:
          * event: the event object sent by Matplotlib
        
        This function finds the data set corresponding to the bars nearest to
        the click point, and draws the corresponding annotation in all the
        connected plots. The drawn annotations consist of a highlighting of
        the bars, and a text (if self.drawtext == True).
        
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
                    self.drawAnnote(event.inaxes, i, j, annote)
                    
                    for l in self.links:
                        l.drawAnnote(l.axis, i, j, annote)
    
    def drawAnnote(self, axis, i, j, annote):
        """Draw an annotation on the plot.
        
        Arguments:
          * axis: the axis to draw on
          * i: the index of the data series for which we're to draw the annote
          * j: the x-index of the bar which is to receive the text-anchor
          * annote: the annotation to draw. It should have an 'id' attribute.
                    The text shown will be formatted using
                    '{}'.format(annote).
        
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
            
            # Shift the color of the bar to highlight it.
            
            color_o = cm.YlOrBr(i / len(self.data))
            color = (color_o[1], color_o[2], color_o[0], color_o[3])
            
            widths = [bins[k + 1] - bins[k] for k in range(len(bins) - 1)]
            m = axis.bar(bins[:-1], heights, widths, bottoms,
                         color=color, edgecolor=(0.0, 0.0, 0.0, 0.0))
            self.drawnAnnotations[annote.id] = (t, m)
            self.axis.figure.canvas.draw()


def linkAnnotationFinders(afs):
    """Link a list of AnnoteFinder|AnnoteFinderBar objects together."""
    for i in range(len(afs)):
        
        allButSelfAfs = afs[:i] + afs[i + 1:]
        afs[i].links.extend(allButSelfAfs)
