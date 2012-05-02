#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc here."""

from __future__ import division

import textwrap
from operator import itemgetter

import pylab as pl
from numpy import random
from matplotlib.container import BarContainer
import matplotlib.cm as cm


class AnnoteFinder(object):
    
    """
    Callback for matplotlib to display an annotation when points are clicked
    on. The point which is closest to the click and within xtol and ytol is
    identified.
      
    Register this function like this:
      
    >>> scatter(xdata, ydata)
    >>> af = AnnoteFinder(xdata, ydata, annotes)
    >>> connect('button_press_event', af)
    
    Methods:
      * __init__:
      * distance:
      * __call__:
      * drawAnnote:
      * drawSpecificAnnote:
    
    """
    
    def __init__(self, xdata, ydata, annotes, axis=None,
                  xtol=None, ytol=None):
        self.data = zip(xdata, ydata, annotes)
        
        if xtol is None:
            xtol = ((max(xdata) - min(xdata)) / float(len(xdata))) / 2
        if ytol is None:
            ytol = ((max(ydata) - min(ydata)) / float(len(ydata))) / 2
        
        self.xtol = xtol
        self.ytol = ytol
        
        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis
        
        self.drawnAnnotations = {}
        self.links = []
    
    def distance(self, x1, x2, y1, y2):
        """Return the distance between two points."""
        return pl.norm(x1 - x2, y1 - y2)
    
    def __call__(self, event):
        if event.inaxes:
            
            clickX = event.xdata
            clickY = event.ydata
            
            if self.axis is None or self.axis == event.inaxes:
                
                annotes = []
                
                for (x, y, a) in self.data:
                    
                    if (clickX - self.xtol < x < clickX + self.xtol and
                        clickY - self.ytol < y < clickY + self.ytol):
                        annotes.append((self.distance(x, clickX, y, clickY),
                                        x, y, a))
                
                if annotes:
                    
                    annotes.sort()
                    x, y, annote = annotes[0][1:]
                    self.drawAnnote(event.inaxes, x, y, annote)
                    
                    for l in self.links:
                        l.drawSpecificAnnote(annote)
    
    def drawAnnote(self, axis, x, y, annote):
        """Draw the annotation on the plot."""
        if (x, y) in self.drawnAnnotations:
            
            markers = self.drawnAnnotations[(x, y)]
            
            for m in markers:
                m.set_visible(not m.get_visible())
            
            self.axis.figure.canvas.draw()
            
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
        annotesToDraw = [(x, y, a) for (x, y, a) in self.data if a == annote]
        for (x, y, a) in annotesToDraw:
            self.drawAnnote(self.axis, x, y, a)


class AnnoteFinderBar(object):
    
    """
    Callback for matplotlib to display an annotation when points are clicked
    on. The point which is closest to the click and within xtol and ytol is
    identified.
      
    Register this function like this:
      
    >>> scatter(xdata, ydata)
    >>> af = AnnoteFinder(xdata, ydata, annotes)
    >>> connect('button_press_event', af)
    
    Methods:
      * __init__:
      * distance:
      * __call__:
      * drawAnnote:
      * drawSpecificAnnote:
    
    """
    
    def __init__(self, l_heights, l_bins, l_bottoms, annotes, axis=None,
                  xtol=None, ytol=None, drawtext=True):
        self.data = zip(l_heights, l_bins, l_bottoms, annotes)
        self.drawtext = drawtext
        
        if xtol is None:
            xtol = min([min(bins) for bins in l_bins]) / 2
        if ytol is None:
            ytol = max([max([t for t in heights + bottoms]) for
                        (heights, bottoms) in zip(l_heights, l_bottoms)]) / 5
        
        self.xtol = xtol
        self.ytol = ytol
        
        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis
        
        self.drawnAnnotations = {}
        self.links = []
    
    def distance(self, x1, x2, y1, y2):
        """Return the distance between two points."""
        return pl.norm([x1 - x2, y1 - y2])
    
    def is_in_bars(self, x, y, heights, bins, bottoms):
        is_in_bars = False
        distances = []
        
        for i in range(len(heights)):
            
            if (bins[i] - self.xtol < x < bins[i + 1] + self.xtol and
                bottoms[i] - self.ytol < y < bottoms[i] + 
                                             heights[i] + self.ytol):
                
                is_in_bars = True
                
                x_dest = (bins[i] + bins[i + 1]) / 2
                
                x_dist = max([0, bins[i] - x, x - bins[i + 1]])
                y_dist = max([0, bottoms[i] - y,
                              y - (bottoms[i] + heights[i])])
                distance = pl.norm([x_dist, y_dist])
                distances.append((distance, x_dest, i))
        
        dxj = sorted(distances)[0] if is_in_bars else None
        return (is_in_bars, dxj)
    
    def __call__(self, event):
        if event.inaxes and pl.get_current_fig_manager().toolbar.mode == '':
            
            clickX = event.xdata
            clickY = event.ydata
            
            if self.axis is None or self.axis == event.inaxes:
                
                annotes = []
                
                for (i, (heights, bins, bottoms, a)) in enumerate(self.data):
                    
                    (is_in_bars, dxj) = self.is_in_bars(clickX, clickY,
                                                        heights, bins,
                                                        bottoms)
                    if is_in_bars:
                        (d, x, j) = dxj
                        annotes.append((d, x, i, j, a))
                
                if annotes:
                    
                    (x, i, j, annote) = sorted(annotes, 
                                               key=itemgetter(0))[0][1:]
                    self.drawAnnote(event.inaxes, x, i, j, annote)
                    
                    for l in self.links:
                        l.drawAnnote(l.axis, x, i, j, annote)
    
    def drawAnnote(self, axis, x, i, j, annote):
        """Draw the annotation on the plot."""
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
            
        else:
            (heights, bins, bottoms) = self.data[i][:3]
            y = bottoms[j] + heights[j] / 2
            
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
            
            widths = [bins[i + 1] - bins[i] for i in range(len(bins) - 1)]
            random.seed(int(annote.id))
            color = cm.hsv(random.random(), alpha=0.8)
            m = axis.bar(bins[:-1], heights, widths, bottoms,
                         color=color, edgecolor=(0.0, 0.0, 0.0, 0.0))
            self.drawnAnnotations[annote.id] = (t, m)
            self.axis.figure.canvas.draw()


def linkAnnotationFinders(afs):
    for i in range(len(afs)):
        
        allButSelfAfs = afs[:i] + afs[i + 1:]
        afs[i].links.extend(allButSelfAfs)
