#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Add annotations to a plot.

"""


from __future__ import division

from abc import ABCMeta, abstractmethod

import pylab as pl


class BaseAnnoteFinder(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self, data, annotes, axis=None):
        
        self.data = data
        self.annotes = annotes
        self.annotes_markers = {}
        self.drawn_annotes = set([])
        
        # Set the axes.
        
        if axis is None:
            self.axis = pl.gca()
        else:
            self.axis = axis
    
    def distance(self, (x1, x2), (y1, y2)):
        """Compute the distance between two points."""
        return pl.norm([x1 - x2, y1 - y2])
    
    def toggle_indrawn(self, an_idx):
        if an_idx in self.drawn_annotes:
            self.drawn_annotes.remove(an_idx)
        else:
            self.drawn_annotes.add(an_idx)
    
    def __call__(self, event):
        
        # Only if we're in the axes, and we're not zooming or in another mode.
        
        if event.inaxes and pl.get_current_fig_manager().toolbar.mode == '':
            
            xc = event.xdata
            yc = event.ydata
            
            # Only if we're in our axes.
            
            if self.axis is None or self.axis == event.inaxes:
                
                for action, params in self.iter_actions((xc, yc)):
                    action(**params)
                
                self.update_graphs()
    
    @abstractmethod
    def iter_actions(self, (xc, yc)):
        raise NotImplementedError
    
    @abstractmethod
    def update_graphs(self):
        raise NotImplementedError


class AnnoteFinderPoint(BaseAnnoteFinder):
    
    def __init__(self, xdata, ydata, annotes, formatter, xtol=None,
                  ytol=None, unique=False, axis=None):
        
        self.unique = unique
        self.formatter = formatter
        
        # Set the tolerances.
        
        if xtol is None:
            xtol = (max(xdata) - min(xdata)) / (2 * float(len(xdata)))
        if ytol is None:
            ytol = (max(ydata) - min(ydata)) / (2 * float(len(ydata)))
        
        self.xtol = xtol
        self.ytol = ytol
        
        super(AnnoteFinderPoint, self).__init__(zip(xdata, ydata), annotes,
                                                axis)
    
    def update_graphs(self):
        self.axis.figure.canvas.draw()
    
    def iter_actions(self, (xc, yc)):
        
        # Find if an annote was caught by the click.
        
        idx = []
        distances = []
        
        for i, (xd, yd) in enumerate(self.data):
            
            if (xc - self.xtol <= xd <= xc + self.xtol and
                yc - self.ytol <= yd <= yc + self.ytol):
                
                idx.append(i)
                distances.append(self.distance((xc, xd), (yc, yd)))
        
        if len(idx) > 0:
            
            annote_idx = idx[pl.argmin(distances)]
            
            # If asked to, remove all other annotes. Careful to do this
            # before yielding the annote to draw as it might need a clean
            # figure to work on.
            
            if self.unique:
                
                for an_idx in self.drawn_annotes.difference([annote_idx]):
                    yield self.toggle_annote, {'an_idx': an_idx,
                                               'xyd': (None, None)}
            
            yield self.toggle_annote, {'an_idx': annote_idx,
                                       'xyd': self.data[annote_idx]}
    
    def toggle_annote(self, an_idx, xyd):
        
        xd, yd = xyd
        
        if self.annotes_markers.has_key(an_idx):
            
            for m in self.annotes_markers[an_idx]:
                m.set_visible(not m.get_visible())
            
            self.toggle_indrawn(an_idx)
            return
        
        t = self.axis.annotate('({}, {})\n{}'.format(xd, yd,
                                     self.formatter(self.annotes[an_idx])),
                           xy=(xd, yd), xycoords='data', xytext=(0, -100),
                           textcoords='offset points',
                           bbox=dict(boxstyle='round',
                                     fc=(0.95, 0.8, 1.0, 0.8),
                                     ec=(0.85, 0.4, 1.0, 0.8)),
                           arrowprops=dict(arrowstyle='wedge,tail_width=1.',
                                           fc=(0.95, 0.8, 1.0, 0.8),
                                           ec=(0.85, 0.4, 1.0, 0.8),
                                           patchA=None, patchB=None,
                                           relpos=(0.1, 1.0),
                                           connectionstyle='arc3,rad=0'))
        p = self.axis.plot([xd], [yd], marker='o', color='yellow',
                           zorder=100, markersize=10)[0]
        self.annotes_markers[an_idx] = [t, p]
        self.drawn_annotes.add(an_idx)


class AnnoteFinderPointPlot(AnnoteFinderPoint):
    
    def __init__(self, xdata, ydata, annotes, formatter, side_plotter,
                  xtol=None, ytol=None, axis=None):
        
        self.side_fig = None
        self.side_plotter = side_plotter
        
        super(AnnoteFinderPointPlot, self).__init__(xdata, ydata, annotes,
                                                    formatter, xtol=xtol,
                                                    ytol=ytol, unique=True,
                                                    axis=axis)
    
    def update_graphs(self):
        super(AnnoteFinderPointPlot, self).update_graphs()
        if self.side_fig and pl.fignum_exists(self.side_fig.number):
            self.side_fig.canvas.draw()
    
    def _toggle_side_fig_ax(self, ax):
        
        if ax in self.side_fig.axes:
            self.side_fig.delaxes(ax)
        
        else:
            
            if not pl.fignum_exists(self.side_fig.number):
                self.side_fig = pl.figure()
                self.side_fig.show()
            
            ax.set_figure(self.side_fig)
            self.side_fig.add_axes(ax)
    
    def toggle_annote(self, an_idx, xyd):
        
        xd, yd = xyd
        
        if self.side_fig == None:
            self.side_fig = pl.figure()
            self.side_fig.show()
        
        if self.annotes_markers.has_key(an_idx):
            
            for m in self.annotes_markers[an_idx]['main_markers']:
                m.set_visible(not m.get_visible())
            
            for ax in self.annotes_markers[an_idx]['side_axes']:
                
                ax.set_visible(not ax.get_visible())
                self._toggle_side_fig_ax(ax)
            
            self.toggle_indrawn(an_idx)
            return
        
        if not pl.fignum_exists(self.side_fig.number):
            self.side_fig = pl.figure()
            self.side_fig.show()
        
        t = self.axis.annotate('({}, {})\n{}'.format(xd, yd,
                                     self.formatter(self.annotes[an_idx])),
                           xy=(xd, yd), xycoords='data', xytext=(0, -100),
                           textcoords='offset points',
                           bbox=dict(boxstyle='round',
                                     fc=(0.95, 0.8, 1.0, 0.8),
                                     ec=(0.85, 0.4, 1.0, 0.8)),
                           arrowprops=dict(arrowstyle='wedge,tail_width=1.',
                                           fc=(0.95, 0.8, 1.0, 0.8),
                                           ec=(0.85, 0.4, 1.0, 0.8),
                                           patchA=None, patchB=None,
                                           relpos=(0.1, 1.0),
                                           connectionstyle='arc3,rad=0'))
        p = self.axis.plot([xd], [yd], marker='o', color='yellow',
                           zorder=100, markersize=10)[0]
        
        # This will create _new_ axes for self.side_fig only if self.side_fig
        # has no axes attached, that is if all previous axes have been cleaned
        # beforehand. This works because removing other annotes is done before
        # adding new annotes in AnnoteFinderPoint.iter_actions.
        
        axes = self.side_plotter(self.side_fig, self.annotes[an_idx])
        
        self.annotes_markers[an_idx] = {'main_markers': [t, p],
                                        'side_axes': axes}
        self.drawn_annotes.add(an_idx)
