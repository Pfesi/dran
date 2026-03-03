# =========================================================================== #
# File: main_gui_logic.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Standard library imports
# --------------------------------------------------------------------------- #
from __future__ import annotations
from PyQt5 import QtWidgets
# from typing import Tuple, Union
# import pandas as pd

import matplotlib.pyplot as pl
# import shutil
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from .canvas_manager import CanvasManager
from .secondary_canvas_manager import SecondaryCanvasManager
from .main_window import Ui_MainWindow
from .edit_driftscan_window import Ui_DriftscanWindow
# =========================================================================== #


class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Main application window handling GUI operations and core functionality.
    
    Args:
        log: Logger instance for application logging
    """

    def __init__(self, log, pathToSaveDir):
        super().__init__()
        self.setupUi(self)
        
        # Initialize 
        self.log = log
        self._initialize_application_state()
        self._setup_components()
        
    def _initialize_application_state(self):
        """Initialize all application state variables."""
        self.file_path = ""  # Current active file path
        self.deleted_items = []  # Track deleted items for undo functionality
        self.initial_status = [0, 0, 0, 0, 0, 0]  # Default status values
        
        # -- Snapshot + printout --
        state = {
            "file_path": self.file_path,
            "deleted_items": list(self.deleted_items),   # copy for safe display
            "initial_status": list(self.initial_status), # copy for safe display
        }

        self.log.info("[INIT] Application state initialized:")
        for k, v in state.items():
            self.log.info(f"  - {k}: {v}")

        return state
    
    def _setup_components(self):
        """Initialize and configure all UI components."""
        
        self.setup_initial_state()
        # self.setup_file_handler()
        
    def setup_initial_state(self):
        """Sets up the initial state of the GUI based on the file path."""
        
        print('\n***** Running setup_initial_state\n')
        if not self.file_path:
            self.set_button_properties(self.btn_edit_driftscan, "white", "black")
            self.set_button_properties(self.btn_edit_timeseries, "white", "black")
            
            self.btn_edit_driftscan.clicked.connect(self.open_drift_window)
            # self.btn_edit_timeseries.clicked.connect(self.open_timeseries_window)
        else:
            # self.open_drift_window()
            pass
        
    def set_button_properties(self, button, bg_color, text_color):
        """Sets the background color and text color of a button."""

        # print('\n***** Running set_button_properties\n')
        button.setStyleSheet(f"QPushButton {{background-color: {bg_color}; color: {text_color};}}")

    def open_drift_window(self):
        """ Connect the edit drift scan window to the main window. """

        # Initiate Canvas
        self.Canvas = CanvasManager(log=self.log)
        self.ntb = NavigationToolbar(self.Canvas, self)
        self.drift_window = QtWidgets.QMainWindow()
        self.drift_ui = Ui_DriftscanWindow()
        self.drift_ui.setupUi(self.drift_window)

        # initiate Secondary canvas
        self.secondaryCanvas = SecondaryCanvasManager(log=self.log)

        # Layouts
        plotLayout = self.drift_ui.PlotLayout
        otherPlotLayout = self.drift_ui.otherPlotsLayout

        # Add Canvas/es to the gui
        plotLayout.addWidget(self.ntb)
        plotLayout.addWidget(self.Canvas)
        otherPlotLayout.addWidget(self.secondaryCanvas)

        # Connect buttons to actions performed by user
        self.connect_buttons()

        # Print welcome message
        self.write("DRAN GUI loaded successfully.",'info')
        self.write("Open a file to get started.",'info')

        # Set status, indicates whether fit/plot has been modified/not
        self.status = [0, 0, 0, 0, 0, 0]

        self.drift_window.show()
        
    