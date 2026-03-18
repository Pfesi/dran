# ============================================================================#
# File: canvas_manager.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# ============================================================================#

# Standard library imports
# --------------------------------------------------------------------------- #
import sys
import numpy as np
import matplotlib as plt
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
# Plot backends
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

# Local imports
# --------------------------------------------------------------------------- #
sys.path.append("src/")
# from common.msgConfiguration import msg_wrapper
# from common.miscellaneousFunctions import reset_list
# =========================================================================== #

class CanvasManager(FigureCanvas):

    """ Manages the plot canvas for the GUI."""

    def __init__(self, parent=None, wid=8, hgt=8, dpi=100, plotName="", log="", cursorState="off"):
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

        self.cursorState = cursorState # turn cursor on/off

        # Create a figure object
        fig = Figure(figsize=(wid, hgt), facecolor='w', edgecolor='k', dpi=dpi)
        grid = gridspec.GridSpec(ncols=2, nrows=7, figure=fig,  right=0.95,
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

    def init_fig_canvas(self):
        """ Initiate layout for the canvases. """

        self.log.debug("Initialize figure canvas")
        
        # Editable plot canvas
        self.ax = self.fig.add_subplot(self.grid[0:5, :])  # (grid[0:3, :])
        self.ax.set_title("Plot canvas")
        self.ax.set_ylabel("Ta [K]")
        self.ax.set_xlabel("Scan dist [deg]")

        # Residuals canvas
        self.ax1 = self.fig.add_subplot(self.grid[6:7, :])
        self.ax1.set_ylabel("res")
        self.ax1.set_xlabel("N")
        self.ax1.set_title("Residuals")

        self.canvases = [self.ax, self.ax1]

    def label_res(self):
        """ Add labels to the residuals"""

        # Residual canvases
        self.ax1.set_ylabel("res")
        self.ax1.set_xlabel("N")
        self.ax1.set_title("Residuals")
        self.draw()

    def label_dual_res(self):
        """ Add labels to the residuals"""

        # Residual canvases
        self.ax1.set_ylabel("res")
        self.ax1.set_xlabel("N")
        self.ax1.set_title("Residuals")

        self.ax2.axes.get_yaxis().set_visible(False) #set_ylabel("Beam B residual")
        self.ax2.set_xlabel("N")
        self.ax2.set_title("Residuals")
        self.draw()

    def init_dual_fig_canvas(self):
        """ Initiate layout for the canvases. """

        # Editable plot canvas
        self.ax = self.fig.add_subplot(self.grid[0:5, :])  # (grid[0:3, :])
        self.ax.set_title("Plot canvas")
        self.ax.set_ylabel("Ta [K]")
        self.ax.set_xlabel("Scan dist [deg]")

        # Residual canvases
        self.ax1 = self.fig.add_subplot(self.grid[6:7, 0:1])
        self.ax1.set_ylabel("res")
        self.ax1.set_xlabel("A beam (N)")
        self.ax1.xaxis.set_major_locator(MaxNLocator())#prune='both'))
        self.ax1.set_title("Residuals A")

        self.ax2 = self.fig.add_subplot(self.grid[6:7, 1:2])
        self.ax2.axes.get_yaxis().set_visible(False) #set_ylabel("Beam B residual")
        self.ax2.set_xlabel("B beam (N)")
        self.ax2.xaxis.set_major_locator(MaxNLocator(prune='both'))
        self.ax2.set_title("Residuals B")

        self.canvases = [self.ax, self.ax1, self.ax2]

    def delete_canvas(self):
        self.fig.clf()

    def clear_canvas(self):
        """ Clear the figure on the Canvas."""

        self.log.debug("Clear the figure on the Canvas.")
        self.clear_figure(self.ax)     # Clear main figure
        self.clear_figure(self.ax1)    # Clear residual figure
    
    def clear_dual_canvas(self):
        """ Clear the figure on the Canvas."""

        self.log.debug("Clear the figure on the Canvas.")
        self.clear_figure(self.ax)     # Clear main figure
        self.clear_figure(self.ax1)    # Clear A beam residual figure
        self.clear_figure(self.ax2)    # Clear B beam residual figure

    def clear_figure(self, ax):
        """ Clear the current figure of the given axis."""
        ax.cla()  # .cla() .gcf().clear()  # which clears data and axes
        self.draw()

    def onmove(self, event):
        """ Track the cursor movement within the figure canvas"""

        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata

        if self.cursorState == "off":
            self.lx.set_visible(False) 
            self.ly.set_visible(False)
        else:
            self.lx.set_visible(True)
            self.ly.set_visible(True)

        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        self.ax.figure.canvas.draw()

    def onpick(self, event):
        """ Pick points on the x-axis where you want to fit your data.
        """

        if isinstance(event.artist, Line2D):
            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            ind = event.ind

            pointsx = xdata[ind]
            pointsy = ydata[ind]

            # Points clicked to plot
            #cursor = Cursor(self.ax, useblit=True, color='red', linewidth=2)
            self.ax.plot(pointsx[0], pointsy[0], 'r.')
            self.log.info(f'picked: {pointsx[0]} @ index: {ind[0]}')

            self.fit_points.append(pointsx[0])
            self.click_index.append(ind[0])
            self.draw()

    def plot_figure(self, x=[], y=[], title="Main plot window", label=""):
        """ Create a figure. """

        self.reset_lists() # Ensure lists are reset for new point/fit selection
        try:
            zero = np.zeros(len(x))     # Create a y=zero line
        except TypeError:
            print("The file you are trying to process is corrupted, please select a different file.")
            sys.exit()

        if len(x) == 0:
            self.clear_figure(self.ax)
            self.set_labels(self.ax, title)

        else:
            self.clear_figure(self.ax)
            self.ax.plot(x, y, label=label, picker=1)
            self.ax.plot(x, zero, 'k')
            self.set_labels(self.ax, title)

            # Add click event handler
            self.lx = self.ax.axhline(color="r")  # the horiz line
            self.ly = self.ax.axvline(color="r")  # the vert line
 
            cid0 = self.mpl_connect('motion_notify_event', self.onmove)
            cid1 = self.mpl_connect('pick_event', self.onpick)

        self.draw()

    def set_labels(self, ax, title="My title", xlabel="Dist [Deg]", ylabel="Ta [K]"):
        """ Set labels for basic plot. """

        ax.set_title(title, fontsize='x-large')  # pad=3
        ax.set_ylabel(ylabel, fontsize="medium")
        ax.set_xlabel(xlabel, fontsize="medium")
        ax.legend(loc="best", fontsize="small", fancybox=True, framealpha=0.5)

    def plot_residual(self, x=[], title="Residuals", label=""):
        """ Plot the residuals"""

        self.clear_figure(self.ax1)

        if len(x) == 0:
            self.ax1.set_title(title)
        else:
            pass

        self.ax1.plot(x, label=label)
        self.ax1.set_xlabel("N", fontsize="medium")
        self.ax1.set_ylabel("res", fontsize="medium")
        self.ax1.legend(loc="best", fontsize="small",
                        fancybox=True, framealpha=0.5)
        self.draw()

    def plot_dual_residuals(self, x1,x2, title="Residuals", label=""):
        """ Plot the residuals """

        self.clear_figure(self.ax1)
        self.clear_figure(self.ax2)

        self.ax1.plot(x1, label=label)
        self.ax2.plot(x2, label=label)

        self.ax1.set_xlabel("A beam (N)", fontsize="medium")
        self.ax2.set_xlabel("B beam (N)", fontsize="medium")

        self.ax1.set_ylabel("res", fontsize="medium")
        self.ax1.legend(loc="best", fontsize="small",
                        fancybox=True, framealpha=0.5)
        self.ax2.legend(loc="best", fontsize="small",
                        fancybox=True, framealpha=0.5)
        self.draw()

    def plot_dual_peaks(self, xpA, ypA, peakA, rmsA, xpB, ypB, peakB, rmsB, x=[], y=[], title="Peak fitted data"):
        """ plot peak fits overlayed on drift scans. """

        self.fit_points = []    # List of points selected for fitting
        self.click_index = []   # List of Index of point selected for fitting

        if len(x) == 0:
            # msg_wrapper("info", self.log.debug, "This plot has no data")
            pass
        else:
            self.ax.plot(x, y, label="data", picker=1)
            self.ax.plot(x, np.zeros_like(x), 'k')
            self.ax.plot(
                xpA, ypA, 'r', label='Fit: Ta[K] = %.3f +- %.3f' % (peakA, rmsA))
            # msg_wrapper("info", self.log.debug,
            #             'Fit: Ta[K]= % .3f + - % .3f' % (peakA, rmsA))
            self.ax.plot(
                xpB, ypB, 'r', label='Fit: Ta[K] = %.3f +- %.3f' % (peakB, rmsB))
            # msg_wrapper("info", self.log.debug,
            #             'Fit: Ta[K]= % .3f + - % .3f' % (peakB, rmsB))
        self.ax.set_title(title)
        self.ax.set_ylabel("Ta [K]")
        self.ax.set_xlabel("Dist [Deg]")
        self.ax.legend(loc="best")

        self.ax1.set_xlabel("A beam (N)", fontsize="medium")
        self.ax2.set_xlabel("B beam (N)", fontsize="medium")
        self.ax1.set_ylabel("res", fontsize="medium")

        self.draw()

    def plot_peak(self, xp, yp, peak, rms, x=[], y=[], title="Peak fitted data"):
        """ Pleat peak fit overlayed on drift scan. """

        self.fit_points = []    # List of points selected for fitting
        self.click_index = []   # List of Index of point selected for fitting

        if len(x) == 0:
            # msg_wrapper("info", self.log.debug, "This plot has no data")
            pass
        else:
            self.ax.plot(x, y, label="data", picker=1)
            self.ax.plot(x, np.zeros_like(x), 'k')
            self.ax.plot(
                xp, yp, 'r', label='Fit: Ta[K] = %.3f +- %.3f' % (peak, rms))
            # msg_wrapper("info", self.log.debug, 'Fit: Ta[K]= % .3f + - % .3f' % (peak, rms))
        self.ax.set_title(title)
        self.ax.set_ylabel("Ta [K]")
        self.ax.set_xlabel("Dist [Deg]")
        self.ax.legend(loc="best")
        
        self.draw()
