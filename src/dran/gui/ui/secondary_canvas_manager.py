# ============================================================================#
# File: secondaryCanvasManager.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# ============================================================================#

# Standard library imports
# --------------------------------------------------------------------------- #
import sys
import numpy as np
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
# Plot backends
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
# from matplotlib.lines import Line2D
# from matplotlib.ticker import MaxNLocator

import warnings

def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()
# =========================================================================== #

class SecondaryCanvasManager(FigureCanvas):

    """ Manages the plot canvas for the GUI."""

    def __init__(self, parent=None, wid=5, hgt=6, dpi=100, plotName="", log=""):
        """
            Initialize an empty canvas for all plots.

            Args:
                parent: the parent figure 
                wid: width of figure
                hgt: height of figure
                dpi: dots per inch of figure
                plotName: name of the figure or figure title
                log: logging object
                cursorState: state of the cursor object, either on or off.
        """

        if log=="":
            self.log = print
        else:
            self.log = log

        # Create a figure object
        fig = Figure(figsize=(wid, hgt), facecolor='w', edgecolor='k', dpi=dpi)
        grid = gridspec.GridSpec(ncols=1, nrows=6, figure=fig,  right=0.95,
                                 top=0.9, bottom=0.1, wspace=0.05, hspace=0.2)   
        
        # Set fitting to zero
        self.reset_lists()

        # Initialize the figure onto the canvas
        FigureCanvas.__init__(self, fig)
        self.fig=fig
        self.grid=grid

        self.setParent(parent)

    def reset_lists(self):
        """
        Setup/reset lists to store data for the click_index and fit_points.

        Args:
            click_index : the indeces of the points clicked on the figure.
            fit_points: the values of the click_index
        """

        self.log.debug("Reset fit points")
        self.click_index = []   # Indeces of clicked points along x-axis
        self.fit_points = []    # Points to be fit/modelled

    def init_canvas(self):
        """ Initiate layout for the canvases. """

        # Editable plot canvas
        self.ax = self.fig.add_subplot(self.grid[0:2, :])  # (grid[0:3, :])
        self.ax.set_title("Raw plots")
        self.ax.set_ylabel("Ta [K]")
        #self.ax.set_xlabel("Scan dist [deg]")

        # Residuals canvas
        self.ax1 = self.fig.add_subplot(self.grid[3:5, :])
        self.ax1.set_ylabel("Ta [K]")
        self.ax1.set_xlabel("Scan dist [deg]")

        self.canvases = [self.ax, self.ax1]

    def clear_canvas(self):
        """ Clear the figure on the Canvas."""

        self.log.debug("Clear the figure on the Canvas.")
        self.clear_figure()     # Clear main figure

    def clear_figure(self):
        """ Clear the current figure of the given axis."""
        self.ax.cla()  # .cla() .gcf().clear()  # which clears data and axes
        self.ax1.cla()
        self.draw()

    def plot_figure(self, x=[], y=[],y1=[], label1="",label2=""):
        """ Create a figure. """

        #self.reset_lists() # Ensure lists are reset for new point/fit selection
        try:
            zero = np.zeros(len(x))     # Create a y=zero line
        except TypeError:
            print("The file you are trying to process is corrupted, please select a different file.")
            sys.exit()

        # if len(x) == 0:
        #     self.clear_figure(self.ax)
        #     self.set_labels(self.ax, title)

        # else:
        self.clear_figure()

        self.ax.plot(x, y, label=label1)
        self.ax.plot(x, zero, 'k')
        self.ax1.plot(x, y1, label=label2)
        self.ax1.plot(x, zero, 'k')

        self.set_labels()
        self.draw()

    def delete_canvas(self):
        self.ax.clf()
        self.ax1.clf()

    def set_labels(self):
        """ Set labels for basic plot. """

        self.ax.set_title('Drift scans', fontsize='medium')  # pad=3
        self.ax.set_ylabel("Ta [K]", fontsize=8)
        self.ax.set_xlabel("ScanDist [deg]", fontsize=8)
        self.ax.legend(loc=1, fontsize=8, fancybox=True, framealpha=0.5)
        self.ax1.set_ylabel("Ta [K]", fontsize=8)
        self.ax1.set_xlabel("ScanDist [deg]", fontsize=8)
        self.ax1.legend(loc=1, fontsize=8, fancybox=True, framealpha=0.5)
