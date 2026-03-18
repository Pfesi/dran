# =========================================================================== #
# File: main_gui_logic.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Standard library imports
# --------------------------------------------------------------------------- #
from __future__ import annotations
from typing import Tuple, Union
import pandas as pd

Scalar = Union[int, float, pd.Timestamp]

# Standard Library Imports
import sys
import os
from datetime import datetime
import datetime as dt
# from sqlalchemy import create_engine

import matplotlib
# matplotlib.use('WebAgg')
matplotlib.use('Qt5Agg')

# Third-Party Library Imports
import matplotlib.dates as mdates 
import numpy as np

# pd.options.mode.copy_on_write = True  # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.set_option("mode.copy_on_write", True)

import matplotlib.pyplot as pl
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg as FigureCanvas, 
 NavigationToolbar2QT as NavigationToolbar)

from PyQt5 import QtWidgets
from astropy.time import Time
import glob
import webbrowser
import sqlite3
from datetime import datetime
from pathlib import Path


# Local Imports
sys.path.append("src/")
from common.msgConfiguration import msg_wrapper
from common.calibrate import (
    _get_pss_values, getpss, calc_dualtotFlux2, add_pss_db,get_fluxes_db,
    calibrate, calc_pc_pss, calc_flux, calc_totFlux, prep_data,
    calc_dualtotFlux, get_fluxes_df, calc_ta_and_ferrs,parse_observation_dates,
    calc_ta_and_ferrs_db, calc_ta_and_ferrs_db2, calc_pss_and_ferrs, calc_pss_and_ferrs_db,
    calc_ta_and_ferrs_fast,add_pss_db_fast2, get_fluxes_db2
)
from common import fitting as fit
from common.file_handler import FileHandler
from common import miscellaneousFunctions as misc

from .main_window import Ui_MainWindow
from .edit_driftscan_window1 import Ui_DriftscanWindow
from .edit_timeseries_window4 import Ui_TimeSeriesWindow
from .view_plots_window import Ui_PlotViewer
from .canvasManager import CanvasManager
from .secondaryCanvasManager import SecondaryCanvasManager
from .timeseries_canvas import TimeCanvas

# =========================================================================== #

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """Main application window handling GUI operations and core functionality.
    
    Args:
        log: Logger instance for application logging
    """

    def __init__(self, log,pathToSaveDir):
        super().__init__()
        self.setupUi(self)

        # Initialize dependencies
        self.log = log
        self.cals=['HYDRA', '3C123', '3C48', '3C161', '3C286','JUPITER'] #'PKS1934','VIRGO',
        self.pathToSaveDir=pathToSaveDir
        
        self._initialize_application_state()
        # sys.exit()
        self._setup_components()
        

        self._get_status()

        print('pathToSaveDir: ',pathToSaveDir)

    # def _initialize_application_state(self):
    #     """Initialize all application state variables."""
    #     self.file_path = ""  # Current active file path
    #     self.deleted_items = []  # Track deleted items for undo functionality
    #     self.initial_status = [0, 0, 0, 0, 0, 0]  # Default status values
        
    def _initialize_application_state(self):
        """
        Initialize application state variables and print their initial values.

        Sets
        ----
        self.file_path : str
            Path to the currently active file (empty when no file is loaded).
        self.deleted_items : list
            Stack/list of deleted items used for undo operations.
        self.initial_status : list[int]
            Status flags or counters; defaults to six zeros.

        Returns
        -------
        dict
            A snapshot of the initialized state for debugging/tests.
        """
        # -- Core state (fresh containers each call) --
        self.file_path = ""                 # Current active file path
        self.deleted_items = []             # Track deleted items for undo functionality
        self.initial_status = [0] * 6       # Default status values

        # -- Pretty logger that falls back to print() --
        logger = getattr(self, "logger", None)
        def _log(msg: str):
            if logger is not None:
                logger.info(msg)
            else:
                print(msg)

        # -- Snapshot + printout --
        state = {
            "file_path": self.file_path,
            "deleted_items": list(self.deleted_items),   # copy for safe display
            "initial_status": list(self.initial_status), # copy for safe display
        }

        _log("[INIT] Application state initialized:")
        for k, v in state.items():
            _log(f"  - {k}: {v}")

        return state


    def _get_status(self):
        print('File path: ',self.file_path)
        print('Deleted items: ',self.deleted_items)
        print('Initial status: ',self.initial_status)

    
    def _setup_components(self):
        """Initialize and configure all UI components."""
        
        self.setup_initial_state()
        self.setup_file_handler()
        # self._connect_signals()

    def setup_initial_state(self):
        """Sets up the initial state of the GUI based on the file path."""
        
        print('\n***** Running setup_initial_state\n')
        if not self.file_path:
            self.set_button_properties(self.btn_edit_driftscan, "white", "black")
            self.set_button_properties(self.btn_edit_timeseries, "white", "black")
            self.set_button_properties(self.btn_view_plots, "white", "black")

            # self.btn_edit_driftscan.clicked.connect(self.open_drift_window)
            self.btn_edit_timeseries.clicked.connect(self.open_timeseries_window)
            # self.btn_view_plots.clicked.connect(self.open_plots_window)
        else:
            # self.open_drift_window()
            pass
        
        self.log.debug("Configured UI for no-file state")

    def setup_file_handler(self):
        print('\n***** Running setup_file_handler\n')
        self.file = FileHandler(self.log)

    def set_button_properties(self, button, bg_color, text_color):
        """Sets the background color and text color of a button."""

        # print('\n***** Running set_button_properties\n')
        button.setStyleSheet(f"QPushButton {{background-color: {bg_color}; color: {text_color};}}")

    def open_timeseries_window(self):
        """Opens the timeseries editing window and initializes its components."""

        print('\n***** Running open_timeseries_window\n')
        self.log.debug("** Initiating timeseries editing window")

        # Create timeseries canvas and navigation toolbar
        self.canvas = TimeCanvas(log=self.log)
        self.ntb = NavigationToolbar(self.canvas, self)

        # Create timeseries window and UI elements
        self.time_window = QtWidgets.QMainWindow()
        self.time_ui = Ui_TimeSeriesWindow()
        self.time_ui.setupUi(self.time_window)

        # Set up layout
        plot_layout = self.time_ui.PlotLayout

        # Add elements to layout
        plot_layout.addWidget(self.ntb)
        plot_layout.addWidget(self.canvas)

        # Configure UI elements for timeseries editing
        self.time_ui.BtnResetPoint.setVisible(False)
        self.time_ui.BtnFit.setVisible(True)
        self.time_ui.BtnQuit.setVisible(False) #.setText("Update db")  # Consider a more descriptive verb
        self.time_ui.EdtSplKnots.setVisible(False)
        self.time_ui.LblSplKnots.setVisible(False)
        self.time_ui.BtnUpdateDB.setVisible(False)
        self.time_ui.BtnDeleteZoomedPoints.setVisible(True)
        self.time_ui.BtnViewZoomedArea.setVisible(True)
        self.time_ui.BtnOpenDB.clicked.connect(self.open_db)
        self.time_ui.comboBoxColsYerr.setVisible(True)

        

        # Hide x-axis limits and y-axis limits for timeseries (optional)
        self.time_ui.Lblxlim.setVisible(False)
        self.time_ui.Lblylim.setVisible(False)

        self.time_ui.EdtxlimMin.setVisible(False)
        self.time_ui.EdtxlimMax.setVisible(False)
        self.time_ui.EdtylimMax.setVisible(False)
        self.time_ui.EdtylimMin.setVisible(False)
        self.time_ui.BtnFilter.setEnabled(False)  # Might need enabling based on context
        self.time_ui.BtnRefreshDB.setVisible(True)
        self.time_ui.BtnSaveDB.setVisible(False)
        self.time_ui.EdtFilter.setEnabled(False)  # Might need enabling based on context
        # Hide date/time pickers if not relevant for timeseries (optional)
        self.time_ui.EdtEndDate.setVisible(False)
        self.time_ui.EdtStartDate.setVisible(False)
        self.time_ui.LblEndDate.setVisible(False)
        self.time_ui.LblStartDate.setVisible(False)

        self.time_ui.BtnDeleteByFilename.setVisible(False)
        self.time_ui.LbLDeleteByFilename.setVisible(False)
        self.time_ui.EdtFilename.setVisible(False)

        # self.time_ui.BtnDeleteZoomedPoints.setVisible(False)
        # self.time_ui.BtnViewZoomedArea.setVisible(False)

        # Connect combo box selection changes
        self.time_ui.comboBoxTables.currentIndexChanged.connect(self.on_table_name_changed)
        # self.time_ui.comboBoxFitTypes.currentIndexChanged.connect(self.on_fit_changed)
        
        
        # self.time_ui.BtnDeleteZoomedPoints.connect(self.delete_zoomed_area)
        # self.time_ui.BtnDelBoth.clicked.connect(self.delete_obs)
        # self.plot_ui.btnDelete.clicked.connect(self.delete_obs)

        # Show the window
        self.time_window.show()
        
    def select_fields(self, key, data_list):
    
        # Define key-to-prefixes mapping
        selected=[]
        
        if key in data_list:
            # print('in')

            key_rules = {
                    'OL':['OL', 'COL', 'NL', 'SL'],
                    'COL':['OL', 'COL', 'NL', 'SL'],
                    'SL':['SL'],
                    'NL':['NL'],
                    'OR':['OR', 'COR', 'NR', 'SR'],
                    'COR':['OR', 'COR', 'NR', 'SR'],
                    'SR':['SR'],
                    'NR':['NR'],

                    'AOL':['AOL', 'ACOL', 'ANL', 'ASL','NL','SL','OL'],
                    'ASL':['ASL','SL'],
                    'ANL':['ANL','NL'],
                    'BOL':['BOL', 'BCOL', 'BNL', 'BSL','NL','SL','OL'],
                    'BSL':['BSL','BL'],
                    'BNL':['BNL','BL'],
                    
                    'AOR':['AOR', 'ACOR', 'ANR', 'ASR', 'NR','SR','OR'],
                    'ASR':['ASR','SR'],
                    'ANR':['ANR','NR'],
                    'BOR':['BOR', 'BCOR', 'BNR', 'BSR','NR','SR','OR'],
                    'BSR':['BSR','BR'],
                    'BNR':['BNR','BR'],

                }

            
            for k,v in key_rules.items():

                if key=='SRC':
                    pass
                else:
                    keyind=len(k)
                    if k==key[:keyind]:

                        prefixes = key_rules[key[:keyind]]

                        for field in data_list:
                            for prefix in prefixes:
                                if field.startswith(prefix) and field!='SRC':
                                    selected.append(field)
                                    
            if len(selected)==0:
                if key in data_list:

                    key_rules = {
                            'ALL':[ 'OL', 'COL', 'NL', 'SL',
                                    'OR', 'COR', 'NR', 'SR',
                                    'AOL', 'ACOL', 'ANL', 'ASL',
                                    'BOL', 'BCOL', 'BNL', 'BSL'
                                    'AOR', 'ACOR', 'ANR', 'ASR',
                                    'BOR', 'BCOR', 'BNR', 'BSR'],
                        }


                    for k,v in key_rules.items():

                        if key=='SRC':
                            pass
                        else:
        #                     keyind=len(k)
        #                     if k==key[:keyind]:

                                prefixes = key_rules['ALL']
    #                             print(prefixes)

                                for field in data_list:
                                    for prefix in prefixes:
                                        if field.startswith(prefix) and field!='SRC':
                                            selected.append(field)
 
        else:
            print(f"{key} key doesn't exist in this list, delete all")

            
        return sorted(selected)
    
    def delete_zoomed_area(self):

        try:
            print('\n', self.zoomed_paths)
            zoomed=True
        except:
            print('No zoomed area selected')
            zoomed=False

        if zoomed==True:
            if len(self.zoomed_paths)==0:
                print('\n Nothing to delete from zoomed area')
            else:
                print('\n Deleting')
                print(self.zoomed_paths)

                self.delZoomed(self.zoomed_paths)
                self.zoomed_paths=[]

    def get_bands(self,band):
        """
        Retrieve the frequency range for a specified satellite band.

        Args:
            band (str): The band identifier (e.g., 'L', 'S', 'C', 'X', 'Ku', 'K', 'Ka').

        Returns:
            dict: A dictionary containing 'start' and 'end' frequencies for the specified band.

        Raises:
            KeyError: If the specified band does not exist.
        """

        # Satellite frequencies obtained from European space agency
        # https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Satellite_frequency_bands


        # Define frequency bands for satellite communications
        FREQUENCY_BANDS = {
            'L': {'start': 1000, 'end': 1999},
            'S': {'start': 2000, 'end': 3999},
            'C': {'start': 4000, 'end': 5999},
            'CM': {'start': 6000, 'end': 7999},  # C-Band, for maser observations
            'X': {'start': 8000, 'end': 11999},
            'Ku': {'start': 12000, 'end': 17999},
            'K': {'start': 18000, 'end': 25999},
            'Ka': {'start': 26000, 'end': 39999},
        }

        try:
            return FREQUENCY_BANDS[band]
        except:
            # Validate input and return the band's frequency range
            print(f"Invalid band: {band}. Valid bands are: {list(FREQUENCY_BANDS.keys())}")
            sys.exit()
            
    
    def add_pss(self,df, caldf,BEAMS,POLARIZATIONS,POSITIONS):
        """
        Calculates and updates PSS (Polarized Source Strength) and related values in the input DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame containing observation data.  Must have columns:
                            'FILENAME', 'OBSDATE', 'time', 'OLTA', 'ORTA', 'id'.
            caldf (pd.DataFrame): Calibration DataFrame containing PSS values. Must have columns:
                                'start', 'end', 'PSS_LCP', 'PSS_LCP_STD', 'PSS_LCP_SE',
                                'PSS_RCP', 'PSS_RCP_STD', 'PSS_RCP_SE'.

        Returns:
            pd.DataFrame: Updated DataFrame with calculated PSS values.
        """

        # Initialize new columns more efficiently
        for b in BEAMS:
            for p in POLARIZATIONS:
                for s in POSITIONS:
                    if s=='O':
                        df[[f'{b}{s}{p}PSS',f'{b}{s}{p}PSSERR',f'{b}{s}{p}CP',f'{b}{s}{p}CPERR']]=np.nan
                    else:
                        df[[f'{b}{s}{p}CP',f'{b}{s}{p}CPERR']]=np.nan
    #     df[['OLPSS', 'OLPSSERR', 'ORPSS', 'ORPSSERR', 'SLCP', 'SLCPERR', 'SRCP', 'SRCPERR', 'STOT', 'STOTERR']] = np.nan

        
        for index, row in df.iterrows():  # Use iterrows for efficient row access
            for b in BEAMS:
                for p in POLARIZATIONS:
                    fn = row['FILENAME']
                    obsdate = str(row['OBSDATE']).split(' ')[0]
                    ta = row[f'{b}CO{p}TA']
                    tae = row[f'{b}CO{p}TAERR']
    #                 orta = row[f'{b}CORTA']
    #                 ortae = row[f'{b}CORTAERR']
                    idx = row['id']

                    # Process OLTA (Left Circular Polarization)
            #         print(obsdate)
                    if pd.notna(ta):  # Use pd.notna for NaN check
                        pss, psse,g = _get_pss_values(caldf, obsdate, f'{b}PSS_{p}CP', f'{b}PSS_{p}CP_SE',f'{p}cp')
                        if pd.notna(pss):
                            df.loc[index, [f'{b}O{p}PSS', f'{b}O{p}PSSERR']] = pss, psse  # More efficient update
    #                         df.loc[index, [f'{b}S{p}CP', f'{b}S{p}CPERR']] = calc_flux(ta,tae,pss, psse)#Calculate SLCP directly
    #                 print(f'{b}O{p}PSS', f'{b}O{p}PSSERR',f'{b}S{p}CP', f'{b}S{p}CPERR')
    
        return df


    def _get_pss_values(self, caldf, obsdate, pss_col, pss_err_col):
        """Helper function to find and return PSS values from calibration DataFrame."""
        for _, c2 in caldf.iterrows():
    #         print(c2)
            start = c2['start']
            end = c2['end']
    #         print(start,end)
            if obsdate >= start and obsdate < end:
                
                lpss = c2[pss_col]
                lpsse = c2[pss_err_col]
    #             print(start,obsdate,end,lpss,lpsse,pol)
                if pd.notna(lpss):
                    return abs(lpss), abs(lpsse),np.nan  # Return values directly
                else:
                    # Handle missing PSS, try previous value (if needed)
                    lpss, lpsse,ind= self._get_previous_pss(caldf, start, pss_col, pss_err_col) # removed unused index
                    return lpss, lpsse, ind
        return np.nan, np.nan, np.nan # Return None if no suitable PSS is found

    def _get_previous_pss(self,mydf,latest_date,col,colerr):
        x=mydf[mydf[col]>0]
    #     print(f'>> Cant find pss at {latest_date}, looking at next best pss')
    #     sys.exit()
        y=x[x['start']<=latest_date]
    #     print(y)
    #     sys.exit()

        if len(y)==0:
    #         print('No previous pss found\n')
            return np.nan, np.nan, np.nan
        else:
    #         print(f'found next best at {y.iloc[-1]} FOR DATE {latest_date}, {col}')
    #         sys.exit()
            pss=y.iloc[-1][col]
            psserr=y.iloc[-1][colerr]
            ind=1#int(y.iloc[-1]['ind'])
            return abs(pss),abs(psserr),ind
        
    def delZoomed(self,paths):
        """Clear selected columns in dataframe for observations matching the given paths."""
        
        # Get selected Y column and corresponding fields to clear
        y_col = self.time_ui.comboBoxColsY.currentText()
        field_names = self.select_fields(y_col, self.df.columns)

        print(f"\nFields to clear for {y_col}:\n{field_names}\n")

        # Pre-process paths for efficient matching
        # path_data = []
        # print('\npaths: ',paths)

        for p in paths:
            base, ext = os.path.splitext(p)
            pname= (base.split('/')[-1])[:18]

            # tag="_".join(p.split("_")[-2:])
            # img_tag, ext = os.path.splitext(tag)

            # base, ext = os.path.splitext(p) # Remove the extension
            parts = base.split('_') # Split by underscore
                
            if parts[-2].startswith('H'):
                start=parts[-2][-1]+parts[-1][0]
            else:
                start=parts[-2][0]+parts[-1][0]
            
            print('start: ',start)

            for index,row in self.df.iterrows():
                # print(index,pname,row['FILENAME'])
                if pname==row['FILENAME'][:18]:
                    print(f'\nFor observation: {pname}')

                    if row[f'{start}FLAG']:
                        row[f'{start}FLAG'] = 200
                        self.df.at[index, f'{start}FLAG'] = 200
                        print('Updated: ',f'{start}FLAG',' = ',row[f'{start}FLAG'])

                    for col in field_names:
                        row[col] = None
                        self.df.at[index, col] = None
                        print('Updated: ',col,' = ',row[col])
                  
        freq=int(self.df['CENTFREQ'].iloc[-1])
        frq=self.table.split("_")[-1]
        print(self.df['BEAMTYPE'].iloc[-1])
        cols=[c for c in self.df.columns]

        pol=['L','R']
        
        calSrc=False
        for col in cols:
            if 'FLUX' in col:
                calSrc=True
        
        if calSrc == True:
            print(f'Im a cal: ',calSrc,self.df['SRC'].iloc[-1])
            sys.exit()

            if self.df['BEAMTYPE'].iloc[-1] == 'SBN':

                pos=['S','N','O'] # hps,hpn,on
                print([c for c in self.df.columns])
                calc_ta_and_ferrs(self.df,pol,pos)

                # check if PSS needs recalculating
                for c in self.df.columns:
                    if 'PSS' in c:
                        print('recalculate PSS')
                        calc_pss_and_ferrs(self.df,pol,pos)
                        break

            elif  self.df['BEAMTYPE'].iloc[-1] == 'DB':
                beams=['A','B']
                pos=['S','N','O'] # hps,hpn,on
                calc_ta_and_ferrs_db(self.df,pol,pos,beams)

                # check if PSS needs recalculating
                for c in self.df.columns:
                    if 'PSS' in c:
                        print('recalculate PSS')
                        calc_pss_and_ferrs_db(self.df,pol,pos,beams)
                        break

        else:
        
            if self.df['BEAMTYPE'].iloc[-1] == 'SBN':

                pos=['S','N','O'] # hps,hpn,on
                print([c for c in self.df.columns])
                calc_ta_and_ferrs(self.df,pol,pos)

            elif  self.df['BEAMTYPE'].iloc[-1] == 'DB':
                beams=['A','B']
                pos=['S','N','O'] # hps,hpn,on
                calc_ta_and_ferrs_db(self.df,pol,pos,beams)
                
            for col in self.df.columns:
            #         print(type(list(df[col])).__name__,col)
                if 'OUT' in col or 'SUM' in col \
                    or col=='n' or col.startswith('fin') \
                    or 'DATA' in col or 'FERR' in col or col=='n' or col=='s':
                    self.df.drop(col,axis=1,inplace=True)

        print([c for c in self.df.columns])
        print(f'\nUpdating table "{self.table}" in database "{self.dbFile}"\n')
        
        # sys.exit()
        # recalculate corrected ta
        self.update_db()
        
        # print(self.df)
        self.canvas.clear_figure()
        self.plot_cols(self.canvas.xlab, self.canvas.ylab)

    # ====================================================================================
    # database operations
    # ====================================================================================
    def _load_database_tables(self,table: str=''):
        """Load tables from database and initialize main dataframe."""

        print('Enter: _load_database_tables')

        if not hasattr(self, "dbFile") or not self.dbFile:
            raise ValueError("Database file not set. Call open_db() first.")

        # Use context manager; avoid double-close
        with sqlite3.connect(self.dbFile) as cnx:
            if not table:
                dbTableList = pd.read_sql_query( "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                cnx
                )
            
                self.tables = sorted(dbTableList['name'].tolist())
            
                if not self.tables:
                    raise ValueError("No valid tables found in database")
                self.table = self.tables[0]
            else:
                self.table=table

            print('Reading from: ',self.table)

            # # Parse OBSDATE as datetime if present (faster than parsing later)
            # try:
            #     self.df = pd.read_sql_query(f"SELECT * FROM '{self.table}'", cnx, parse_dates=["OBSDATE"])
            # except Exception:
            self.df = pd.read_sql_query(f"SELECT * FROM '{self.table}'", cnx)


        print('+++++ ',self.table)
        self.orig_df = self.df.copy()
        print([c for c in self.df.columns])
        self._prep_data()
        print(list(self.df.columns))
        print('Exit: _load_database_tables')

    def update_db(self):
        # WAL can speed concurrent readers; NORMAL is a reasonable sync
        with sqlite3.connect(self.dbFile) as cnx:
            cnx.execute("PRAGMA journal_mode=WAL;")
            cnx.execute("PRAGMA synchronous=NORMAL;")
            self.df.to_sql(self.table, cnx, if_exists='replace', index=False)
        print('Updated db')
    # ====================================================================================

    # ====================================================================================
    # web/html operations
    # ====================================================================================
    # src/your_project/data/select.py
    def zoom_slice(df: pd.DataFrame, x: str, y: str,
                xlim: Tuple[Scalar, Scalar],
                ylim: Tuple[float, float]) -> pd.DataFrame:
        
        """Vectorized, dtype-safe zoom selection."""
        x0, x1 = xlim
        y0, y1 = ylim
        # If OBSDATE is datetime-like, ensure dtype once upstream (faster overall).
        mx = df[x].between(x0, x1, inclusive="both")
        my = df[y].between(y0, y1, inclusive="both")
        return df.loc[mx & my]

    def list_images(self, folder: Path, exts=(".png", ".jpg", ".jpeg", ".webp")):
        ex = {e.lower() for e in exts}
        return sorted(p for p in folder.iterdir() if p.suffix.lower() in ex)

    # src/your_project/web/html.py
    def card(self, img_uri: str, title: str, subtitle: str) -> str:
        return f"""
            <div class="card">
            <div class="card-body">
                <h5 class="card-title">{title}</h5>
                <p class="card-text">{subtitle}</p>
                <a target="_blank" href="{img_uri}">
                <img src="{img_uri}" class="card-img-top" alt="{title}">
                </a>
                <div class="d-grid gap-2 mt-3">
                <button class="btn btn-outline-danger btn-sm delete-btn"
                        data-img="{img_uri}" data-title="{title}">Delete</button>
                </div>
            </div>
            </div>
            """
    # ====================================================================================

    def _configure_button(self, button, background_color, text_color):
        """Helper method to standardize button styling.
        
        Args:
            button: QPushButton to configure
            background_color: str color name or hex value
            text_color: str color name or hex value
        """
        button.setStyleSheet(
            f"QPushButton {{ background-color: {background_color}; color: {text_color}; }}"
        )
        button.setEnabled(True)

    def open_db(self):
        """Open and process a SQLite database file, initializing UI components and data structures."""


        print('\n***** Running open_db\n')

        # Get the database file path
        # self.dbFile='/Users/pfesesanivanzyl/dran/HART26DATA.db'#resultsFromAnalysis/JUPITER/JUPITER.db'
        self.dbFile = self.open_file_name_dialog("*.db")
        # self.dbFile='/Users/pfesesanivanzyl/dran-analysis/resultsFromAnalysis/3C48/3C48.db'#resultsFromAnalysis/JUPITER/JUPITER.db'
        # self.dbFile='/Users/pfesesanivanzyl/dran/CALDB.db' #-analysis/resultsFromAnalysis/3C48/3C48.db'#resultsFromAnalysis/JUPITER/JUPITER.db'
        # self.dbFile='/Users/pfesesanivanzyl/dran/resultsFromAnalysis/HYDRAA/HYDRAA.db'

        # Validate file selection
        if not self.dbFile:
            print("No file selected")
            return

        # Verify file exists
        if os.path.isfile(self.dbFile):
            pass
        else:
            print(f'File: "{self.dbFile}" does not exists\n')
            sys.exit() 

        # Update UI with database path
        self.time_ui.EdtDB.setText(self.dbFile)
        self.time_ui.EdtDB.setEnabled(True)

        self.time_ui.BtnDeleteByFilename.setVisible(True)
        self.time_ui.LbLDeleteByFilename.setVisible(True)
        self.time_ui.EdtFilename.setVisible(True)
        
        # Log database opening
        msg_wrapper("debug", self.log.debug, f"\nOpening database: {self.dbFile}")
        
        # Connect to database and process data
        self._load_database_tables()

        # Update UI components
        self._update_ui_components()
            
        self._finalize_setup()

       
    def _finalize_setup(self):
        """Finalize UI and event connections."""
        self.enable_time_buttons()
        self.populate_cols()
        self.connect_ui_events()

    def populate_cols(self,xcol='',ycol='',yerrcol='',table=''):
        """Fetches data from the database and populates UI elements."""
        
        print('\n***** Running populate_cols\n')
        # create dataframe from current database table -> self.df

        if table:
            self._load_database_tables(table=table)

        # Handle empty table selection
        self.table = self.time_ui.comboBoxTables.currentText()
        print('tables: ',self.tables)
        # sys.exit()

        if not self.table:
            self._update_ui_components()
            self.table = self.time_ui.comboBoxTables.currentText()

        self.colNames = self.df.columns.tolist()

        # exclude the following columns from plotting
        plotCols=[]
        for name in self.colNames:
            if 'id' in name  or 'LOGFREQ' in name or 'CURDATETIME' in name or \
                'FILE' in name or 'OBSD' in name \
                    or 'MJD' in name or 'OBS' in name or 'OBJ' in name or 'id' == name \
                        or 'RAD' in name or 'TYPE' in name or 'PRO' in name or 'TELE' in\
                              name or 'UPGR' in name  or 'INST' in name or \
                                'SCANDIR' in name or 'SRC' in name or 'COORDSYS' in name or 'LONGITUD' in name \
                                    or 'LATITUDE' in name  or 'POINTING' in name \
                                       or 'DICHROIC' in name \
                                            or 'PHASECAL' in name or 'HPBW' in name or 'FNBW' in name or 'SNBW' in name\
                                                or 'FRONTEND' in name or 'BASE' in name:
                pass
            else:
                plotCols.append(name)
        
        # setup error columns
        errcols=[]
        for name in self.colNames:
            if   'ERR' in name:
                errcols.append(name)
            else:
                pass

        # setup X and Y columns
        xCols=['OBSDATE','MJD','HA','ELEVATION']
        # xCols=xCols+[c for c in self.colNames if 'RMS' in c or 'SLOPE' in c]

        yerr=['None']
        self.yErr=list(yerr)+list(errcols)

        # prep columns
        print('cols: ',xcol,ycol,yerrcol)
        self.time_ui.comboBoxColsX.clear()
        self.time_ui.comboBoxColsX.clear()
        if xcol!='':
            self.time_ui.comboBoxColsX.setCurrentText(xcol)
        else:
            self.time_ui.comboBoxColsX.addItems(xCols)
        self.time_ui.comboBoxColsY.clear()
        self.time_ui.comboBoxColsY.clear()
        if ycol!='':
            self.time_ui.comboBoxColsY.setCurrentText(ycol)
        else:
            self.time_ui.comboBoxColsY.addItems(plotCols)
       
        self.time_ui.comboBoxColsYerr.clear()
        self.time_ui.comboBoxColsYerr.clear()
        if yerrcol!='':
            self.time_ui.comboBoxColsYerr.setCurrentText(yerrcol)
        else:
            self.time_ui.comboBoxColsYerr.addItems(self.yErr)

        # print('cols: ',xcol,ycol,yerrcol)
        # self.time_ui.comboBoxColsX.addItems(xCols)
        # self.time_ui.comboBoxColsY.addItems(plotCols)
        # self.time_ui.comboBoxColsYerr.addItems(self.yErr)

    def on_table_name_changed(self):
        """Update UI components when the selected table changes in the combobox."""
    
        print('\n***** Running on_table_name_changed\n')

        # Get selected table and update dataframe
        table=self.time_ui.comboBoxTables.currentText()
        self._load_database_tables(table)
        # self.create_df_from_db(table)

        # Initialize column lists
        self.colNames = self.df.columns.tolist()
        print('>>>>>  ', self.colNames)
        
        # Process error columns
        # self._process_error_columns()

        # Process X and Y axis columns
        xCols = self._get_x_columns()
        plotCols = self._get_plot_columns()

        print(f'Getting data from table: {table}')

        # Update UI components
        self._update_column_comboboxes(xCols, plotCols)
        
        # Plot with default columns
        self.plot_cols(xcol=xCols[0], ycol=plotCols[0], yerr="")

    def _get_x_columns(self):
        return ['OBSDATE','MJD','HA','ELEVATION']
    
    def _get_plot_columns(self):

        self.colNames = self.df.columns.tolist()

        # exclude the following columns from plotting
        plotCols=[]
        for name in self.colNames:
            if 'id' in name  or 'LOGFREQ' in name or 'CURDATETIME' in name or \
                'FILE' in name or 'OBSD' in name \
                    or 'MJD' in name or 'OBS' in name or 'OBJ' in name or 'id' == name \
                        or 'RAD' in name or 'TYPE' in name or 'PRO' in name or 'TELE' in\
                              name or 'UPGR' in name  or 'INST' in name or \
                                'SCANDIR' in name or 'SRC' in name or 'COORDSYS' in name or 'LONGITUD' in name \
                                    or 'LATITUDE' in name  or 'POINTING' in name \
                                       or 'DICHROIC' in name \
                                            or 'PHASECAL' in name or 'HPBW' in name or 'FNBW' in name or 'SNBW' in name\
                                                or 'FRONTEND' in name or 'BASE' in name:
                pass
            else:
                plotCols.append(name)

        errcols=[]
        for name in self.colNames:
            if   'ERR' in name:
                errcols.append(name)
            else:
                pass

        yerr=['None']
        self.yErr=list(yerr)+list(errcols)

        return plotCols

    def _update_column_comboboxes(self, xCols, plotCols):
        """Update the X, Y, and error column comboboxes in the UI."""
        # Clear and populate X-axis combobox
        self.time_ui.comboBoxColsX.clear()
        self.time_ui.comboBoxColsX.clear()
        self.time_ui.comboBoxColsX.addItems(xCols)
        
        # Clear and populate Y-axis combobox
        self.time_ui.comboBoxColsY.clear()
        self.time_ui.comboBoxColsY.clear()
        self.time_ui.comboBoxColsY.addItems(plotCols)
        
        # Clear and populate error combobox
        self.time_ui.comboBoxColsYerr.clear()
        self.time_ui.comboBoxColsYerr.clear()
        self.time_ui.comboBoxColsYerr.addItems(self.yErr)

    def on_fit_changed(self):
        """  Toggle labels and edit boxes on or off when fit type is changed."""

        print('\n***** Running on_fit_changed\n')
        if self.time_ui.comboBoxFitTypes.currentText()=="Spline":
            self.time_ui.LblSplKnots.setVisible(True)
            self.time_ui.EdtSplKnots.setVisible(True)
            self.time_ui.EdtEndDate.setVisible(False)
            self.time_ui.EdtStartDate.setVisible(False)
            self.time_ui.LblEndDate.setVisible(False)
            self.time_ui.LblStartDate.setVisible(False)
        else:
            self.time_ui.LblSplKnots.setVisible(False)
            self.time_ui.EdtSplKnots.setVisible(False)
            self.time_ui.EdtEndDate.setVisible(True)
            self.time_ui.EdtEndDate.setEnabled(True)
            self.time_ui.EdtStartDate.setVisible(True)
            self.time_ui.EdtStartDate.setEnabled(True)
            self.time_ui.LblEndDate.setVisible(True)
            self.time_ui.LblStartDate.setVisible(True)

    def enable_time_buttons(self):
        """Enable time buttons."""

        print('\n***** Running enable_time_buttons\n')
        for widget_name in [
            "comboBoxTables",
            "comboBoxColsX",
            "comboBoxColsY",
            "comboBoxColsYerr",
            "EdtSplKnots",
            "BtnPlot",
            "comboBoxFilters",
            "EdtFilter",
            "BtnFilter",
            "comboBoxFitTypes",
            "comboBoxOrder",
            "BtnFit",
            "BtnDelPoint",
            "BtnDelBoth",
            "BtnResetPoint",
            "BtnReset",
            "BtnDeleteByFilename",
            "BtnRefreshDB",
            "BtnUpdateDB",
            "BtnSaveDB",
            "BtnDeleteZoomedPoints",
            "BtnViewZoomedArea",
            # "BtnQuit",
        ]:
            getattr(self.time_ui, widget_name).setEnabled(True)

        print('Enabled: enable_time_buttons')

    # --- File operations
    def open_file_name_dialog(self, ext):
        """Opens a file dialog to select a file with the specified extension.

        Args:
            ext: The file extension to filter for.

        Returns:
            The selected file path, or None if no file is selected.
        """

        print('\n***** Running open_file_name_dialog\n')
        msg_wrapper("debug", self.log.debug, "Opening file name dialog")

        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", "", f"Fits Files (*{ext});;Fits Files (*{ext})")

        return file_name
    
    def connect_ui_events(self):
        """Connects all UI signals to their corresponding event handlers.
        
        Organizes connections by functional categories and provides clear debugging.
        """
        self.log.debug("Connecting UI signals to event handlers")
        
        try:
            self._connect_plot_operations()
            self._connect_data_operations()
            self._connect_database_operations()
        except Exception as e:
            self.log.error(f"Failed to connect UI events: {str(e)}")
            raise

        print("Connected: connect_ui_events")

    def _connect_plot_operations(self):
        """Connect signals for plot-related operations."""
        self.time_ui.BtnPlot.clicked.connect(self.plot_cols)
        self.time_ui.BtnViewZoomedArea.clicked.connect(self.view_zoomed_area)
        self.time_ui.BtnDeleteZoomedPoints.clicked.connect(self.delete_zoomed_area)
        # self.time_ui.BtnDeleteZoomedPoints.connect(self.delete_zoomed_area)
        self.time_ui.BtnDelBoth.clicked.connect(self.update_all_points) # delete_obs
        self.time_ui.BtnDelPoint.clicked.connect(self.update_point)
        # self.time_ui.BtnDeleteByFilename.clicked.connect(self.update_by_filename)

    def update_by_filename(self):
        # # print(f'Deleted by filename: {}')

        # filename=self.time_ui.EdtFilename.text()
        # filenames=self.df['FILENAME'].str[:18]
        
        # # if filename in self.df['FILENAME']
        # print(filenames,type(filenames),filenames.index)
        # # print([c for c in self.df['FILENAME']])
        # sys.exit()
        # get data 
        print('Updating table ',self.table)
        self._load_database_tables(self.table)
        # # recalculate corrected ta
        # self.update_db()

        # Clear the plot and re-plot the updated data
        self.canvas.clear_figure()
        self.canvas.clear_figure()
        # self.plot_cols(self.canvas.xlab, self.canvas.ylab)


    def update_point(self):
        """
        Updates the selected point in the database and plot.

        Raises:
            ValueError: If setting a column value to NaN fails.
        """

        print('\n***** Running update_point\n')

        # Retrieve the selected point and corresponding data
        fit_points = self.canvas.fit_points
        click_index = self.canvas.click_index

        # Validate that we have both points and a selected index
        if not fit_points or not click_index:
            print("No point selected.")
            return

        pos = int(click_index[0])  # Point index to delete
        df_row = self.df.iloc[pos]

        # print(df_row)

        # Print confirmation message
        print(f'\nDeleting points from row: {pos}')
        print(f'- Object: {df_row["OBJECT"]}')
        print(f'- Date: {df_row["OBSDATE"].date()}')
        print(f'- Frequency: {df_row["CENTFREQ"]}\n')
        print(f"- (x: {fit_points[0][0]})\n"
              f"- (y: {fit_points[0][1]})\n"
            )

        
        # Update value in DataFrame
        ycol=self.canvas.ylab

        beam=df_row['FRONTEND']

        POLS=['L','R'] # POLARIZATION
        POSITIONS=['S','N','O'] # hps,hpn,on
        BEAMS=['A','B']

        print(f"- (beam: {beam})\n"
              f"- (yCol: {ycol})\n"
            )


        field_names = self.select_fields(ycol, self.df.columns)
        print(f"Fields to clear for {ycol}:\n{field_names}\n")

        

        # for index,row in self.df.iterrows():
        for col in field_names:
            if 'FLAG' in col:
                self.df.at[pos,col]=200
            else:
                self.df.at[pos,col]=np.nan
            print("Updated ",col,': ', self.df.iloc[pos][col])



        calSrc=False
        for c in self.df.columns:
            if 'FLUX' in c:
                print('\nSource is a Target')
                calSrc=True
            
        # print(calSrc)
        
        # df=get_table_from_db(srcDBpath,f'{src}_{f}')
        # df=prep_data(df, src)
        # df=calc_ta_and_ferrs_db(df,pol,pos,BEAMS)#, verbose=True)
        # df=add_pss_db_fast2(df, pss, pol, pos, BEAMS)
        # df=get_fluxes_db2(df)

        # if df_row['OBJECT'] in self.cals:
        if calSrc==True:

            # if "PSS" in c :   
                print('\n> Recalculating PSS for ', df_row['OBJECT'] )
                # sys.exit()

                if df_row['BEAMTYPE']=="SBN":
                    for pol in POLS:
                        try:
                            pss, errPSS, pc, corrTa, errCorrTa, appEff = calc_pc_pss(df_row[f"S{pol}TA"], df_row[f'S{pol}TAERR'], df_row[f"N{pol}TA"], df_row[f"N{pol}TAERR"], df_row[f'O{pol}TA'], df_row[f'O{pol}TAERR'], df_row['TOTAL_PLANET_FLUX_D'], df_row)               
                        except:
                            pss, errPSS, pc, corrTa, errCorrTa, appEff = calc_pc_pss(df_row[f"S{pol}TA"], df_row[f'S{pol}TAERR'], df_row[f"N{pol}TA"], df_row[f"N{pol}TAERR"], df_row[f'O{pol}TA'], df_row[f'O{pol}TAERR'], df_row['FLUX'], df_row)               
                        
                        self.df.at[pos, f"O{pol}PSS"] = pss 
                        self.df.at[pos, f"O{pol}PSSERR"] = errPSS
                        self.df.at[pos, f"O{pol}PC"] = pc 
                        self.df.at[pos, f"CO{pol}TA"] = corrTa
                        self.df.at[pos, f"CO{pol}TAERR"] = errCorrTa

                        print("\nUpdated ", f"O{pol}PSS",': ', self.df.iloc[pos][ f"O{pol}PSS"])
                        print("Updated ", f"O{pol}PSSERR",': ', self.df.iloc[pos][ f"O{pol}PSSERR"])
                        print("Updated ", f"O{pol}PC",': ', self.df.iloc[pos][ f"O{pol}PC"])
                        print("Updated ", f"O{pol}TA",': ', self.df.iloc[pos][ f"O{pol}TA"])
                        print("Updated ", f"O{pol}TAERR",': ', self.df.iloc[pos][ f"O{pol}TAERR"])
                    # break

                if df_row["BEAMTYPE"]=="DB":
                    # check if PSS needs recalculating
                # for c in self.df.columns:
                    # if 'PSS' in c:
                        print('recalculate PSS')
                        calc_pss_and_ferrs_db(self.df,POLS,POSITIONS,BEAMS)
                  
        else:
            print ('Target',ycol, df_row[ycol])

            # recalculate antenna temp
            if df_row["BEAMTYPE"]=="DB":
            #     # S,N,O

                
                # calc_ta_and_ferrs_db(self.df,POLS,POSITIONS,BEAMS)
                # self.df=calc_ta_and_ferrs_fast(self.df,POLS,POSITIONS,BEAMS)
                self.df=calc_ta_and_ferrs_db2(self.df,POLS,POSITIONS,BEAMS)
              
                # print(df_row['CENTFREQ'], f"{self.table}")
                frq=self.table.split("_")[-1]
                pathToCSV=f'/Users/pfesesanivanzyl/software/dran/resultsFromAnalysis/HYDRAA/HYDRAA_{frq}/HYDRAA_{frq}_monthly.csv'
                # print(pathToCSV)

                # get csv data
                try:
                    dfBinned = pd.read_csv(pathToCSV)
                    dfBinned["OBSDATE"] = pd.to_datetime(dfBinned["meanDate"]).dt.date
                except:
                    dfBinned=[]

                # print(dfBinned)
                # self.df = add_pss_db(self.df, dfBinned,POLS,POSITIONS,BEAMS)

                self.df=add_pss_db_fast2(self.df, dfBinned, POLS,POSITIONS, BEAMS)
                self.df=get_fluxes_db2(self.df)
                self.df["OBSDATE"] = pd.to_datetime(self.df["OBSDATE"])#.dt.date


        for col in self.df.columns:
            if 'OUT' in col or 'SUM' in col \
                or col=='N' or col=='n' or col=='s' \
                    or col.startswith('fin') \
                        or 'DATA' in col or 'FERR' in col:
                # print(col)
                self.df.drop(col,axis=1,inplace=True)

        # print([c for c in self.df.columns])


        print(f'\nUpdating table "{self.table}" in database "{self.dbFile}"\n')
        self.update_db()
        
        # pass
        print(self.canvas.xlab, self.canvas.ylab)

        # Clear the plot and re-plot the updated data
        self.canvas.clear_figure()
        self.plot_cols(self.canvas.xlab, self.canvas.ylab)

    def update_all_points(self):
        """
        Updates the database and plot after deleting a point from the DataFrame.

        This function retrieves the selected point, updates the DataFrame and database,
        and then redraws the plot.

        Raises:
            Exception: If an error occurs while connecting to or updating the database.
        """

        print('\n***** Running update_all_points\n')
        # Get selected point and index
        fit_points = self.canvas.fit_points
        click_index = self.canvas.click_index

        if not fit_points or not click_index:
            print("No point selected.")
            return

        # Extract data from DataFrame
        pos = int(click_index[0])  # Point index to delete
        df_row = self.df.iloc[pos]

        print(df_row)
        # Print confirmation message
        print(f'\nDeleting points from row: {pos}')
        print(f'Object: {df_row["OBJECT"]}')
        print(f'Date: {df_row["OBSDATE"].date()}')
        print(f'Frequency: {df_row["CENTFREQ"]}\n')
        print(f"- (x: {fit_points[0][0]})\n"
            f"- (y: {fit_points[0][1]})\n"
            )

        #Deleting points from row: 4
        # Object: 3C48
        # Date: 2025-02-16
        # Frequency: 2270.0

        # - (x: 2025-02-16T00:00:00.000000000)
        # - (y: 5.0)

        # 2270 3C48

        freq=int(df_row['CENTFREQ'])
        srcname=df_row['OBJECT']
        beam=df_row['FRONTEND']

        print(freq,srcname,beam)
        print([c for c in self.df.columns])
        # sys.exit()

        POLS=['L','R'] # POLARIZATION

        if beam == '13.0S':
            #['id', 'FILENAME', 'FILEPATH', 'CURDATETIME', 'MJD', 'OBSDATE',
    #    'OBSTIME', 'OBSDATETIME', 'FRONTEND', 'HDULENGTH', 'OBJECT', 'SRC',
    #    'OBSERVER', 'OBSLOCAL', 'OBSNAME', 'PROJNAME', 'PROPOSAL', 'TELESCOP',
    #    'UPGRADE', 'CENTFREQ', 'BANDWDTH', 'LOGFREQ', 'BEAMTYPE', 'HPBW',
    #    'FNBW', 'SNBW', 'FEEDTYPE', 'LONGITUD', 'LATITUDE', 'COORDSYS',
    #    'EQUINOX', 'RADECSYS', 'FOCUS', 'TILT', 'TAMBIENT', 'PRESSURE',
    #    'HUMIDITY', 'WINDSPD', 'SCANDIR', 'POINTING', 'BMOFFHA', 'BMOFFDEC',
    #    'DICHROIC', 'PHASECAL', 'NOMTSYS', 'SCANDIST', 'SCANTIME', 'INSTRUME',
    #    'INSTFLAG', 'HZPERK1', 'HZKERR1', 'HZPERK2', 'HZKERR2', 'TCAL1',
    #    'TCAL2', 'TSYS1', 'TSYSERR1', 'TSYS2', 'TSYSERR2', 'ELEVATION', 'ZA',
    #    'HA', 'ATMOSABS', 'PWV', 'SVP', 'AVP', 'DPT', 'WVD', 'OLTA', 'OLTAERR',
    #    'OLMIDOFFSET', 'OLS2N', 'OLFLAG', 'OLBRMS', 'OLSLOPE', 'OLBASELEFT',
    #    'OLBASERIGHT', 'OLRMSB', 'OLRMSA', 'ORTA', 'ORTAERR', 'ORMIDOFFSET',
    #    'ORS2N', 'ORFLAG', 'ORBRMS', 'ORSLOPE', 'ORBASELEFT', 'ORBASERIGHT',
    #    'ORRMSB', 'ORRMSA', 'time', 'FLUX', 'OLPSS', 'OLPSSERR', 'OLAPPEFF',
    #    'ORPSS', 'ORPSSERR', 'ORAPPEFF']
            ta=[]
            del_ta=[]

            POSITION=['O']
            
            for l in POLS:
                for p in POSITION:
                    print(f'{p}{l}')
                    ta.append(f'{p}{l}TA')
                    ta.append(f'{p}{l}TAERR')

                    del_ta.append(f'{p}{l}TA')
                    del_ta.append(f'{p}{l}TAERR')
                    del_ta.append(f'{p}{l}S2N')
                    del_ta.append(f'{p}{l}FLAG')
                    del_ta.append(f'{p}{l}BRMS')
                    del_ta.append(f'{p}{l}SLOPE')
                    del_ta.append(f'{p}{l}BASELEFT')
                    del_ta.append(f'{p}{l}BASERIGHT')
                    del_ta.append(f'{p}{l}MIDOFFSET')
                    del_ta.append(f'{p}{l}RMSB')
                    del_ta.append(f'{p}{l}RMSA')    

                    if p=='O':
                        del_ta.append(f'{p}{l}PSS')
                        del_ta.append(f'{p}{l}PSSERR')
                        del_ta.append(f'{p}{l}APPEFF')

                for c in del_ta:
                    try:
                        self.df.at[pos, c] = np.nan
                    except ValueError:
                        self.df.at[pos, c] = 0.0
                        print(f"Warning: Setting df[{c}] to 0.0 instead of NaN")

            # for c in del_ta:
            #     if 'PSS' in c:

            # print(ta,'\n') 
                print(del_ta,'\n') 
                del_ta=[]
                ta=[]

            # sys.exit()
            print(f'\nUpdating table "{self.table}" in database "{self.dbFile}"\n')

            cnx = sqlite3.connect(self.dbFile)
            self.df.to_sql(self.table,cnx,if_exists='replace',index=False)
            cnx.close()
            pass

        elif beam == '01.3S' or beam == '02.5S':
            #['id', 'FILENAME', 'FILEPATH', 'CURDATETIME', 'MJD', 'OBSDATE', 'OBSTIME', 
            # 'OBSDATETIME', 'FRONTEND', 'HDULENGTH', 'OBJECT', 'SRC', 'OBSERVER', 
            # 'OBSLOCAL', 'OBSNAME', 'PROJNAME', 'PROPOSAL', 'TELESCOP', 'UPGRADE', 
            # 'CENTFREQ', 'BANDWDTH', 'LOGFREQ', 'BEAMTYPE', 'HPBW', 'FNBW', 'SNBW', 
            # 'FEEDTYPE', 'LONGITUD', 'LATITUDE', 'COORDSYS', 'EQUINOX', 'RADECSYS', 
            # 'FOCUS', 'TILT', 'TAMBIENT', 'PRESSURE', 'HUMIDITY', 'WINDSPD', 'SCANDIR', 
            # 'POINTING', 'BMOFFHA', 'BMOFFDEC', 'HABMSEP', 'DICHROIC', 'PHASECAL', 'NOMTSYS', 
            # 'SCANDIST', 'SCANTIME', 'INSTRUME', 'INSTFLAG', 'HZPERK1', 'HZKERR1', 'HZPERK2', 
            # 'HZKERR2', 'TCAL1', 'TCAL2', 'TSYS1', 'TSYSERR1', 'TSYS2', 'TSYSERR2', 'ELEVATION', 
            # 'ZA', 'HA', 'PWV', 'SVP', 'AVP', 'DPT', 'WVD', 'HPBW_ARCSEC', 'ADOPTED_PLANET_TB', 
            # 'PLANET_ANG_DIAM', 'JUPITER_DIST_AU', 'SYNCH_FLUX_DENSITY', 'PLANET_ANG_EQ_RAD', 
            # 'PLANET_SOLID_ANG', 'THERMAL_PLANET_FLUX_D', 'TOTAL_PLANET_FLUX_D', 'TOTAL_PLANET_FLUX_D_WMAP', 
            # 'SIZE_FACTOR_IN_BEAM', 'SIZE_CORRECTION_FACTOR', 'MEASURED_TCAL1', 'MEASURED_TCAL2', 
            # 'MEAS_TCAL1_CORR_FACTOR', 'MEAS_TCAL2_CORR_FACTOR', 'ATMOS_ABSORPTION_CORR', 'ZA_RAD', 
            # 'TAU221', 'TAU2223', 'TBATMOS221', 'TBATMOS2223', 'NLTA', 'NLTAERR', 'NLMIDOFFSET', 'NLS2N', 
            # 'NLFLAG', 'NLBRMS', 'NLSLOPE', 'NLBASELEFT', 'NLBASERIGHT', 'NLRMSB', 'NLRMSA', 'SLTA', 
            # 'SLTAERR', 'SLMIDOFFSET', 'SLS2N', 'SLFLAG', 'SLBRMS', 'SLSLOPE', 'SLBASELEFT', 'SLBASERIGHT', 
            # 'SLRMSB', 'SLRMSA', 'OLTA', 'OLTAERR', 'OLMIDOFFSET', 'OLS2N', 'OLFLAG', 'OLBRMS', 'OLSLOPE', 
            # 'OLBASELEFT', 'OLBASERIGHT', 'OLRMSB', 'OLRMSA', 'OLPC', 'COLTA', 'COLTAERR', 'NRTA', 'NRTAERR', 
            # 'NRMIDOFFSET', 'NRS2N', 'NRFLAG', 'NRBRMS', 'NRSLOPE', 'NRBASELEFT', 'NRBASERIGHT', 'NRRMSB', 
            # 'NRRMSA', 'SRTA', 'SRTAERR', 'SRMIDOFFSET', 'SRS2N', 'SRFLAG', 'SRBRMS', 'SRSLOPE', 'SRBASELEFT', 
            # 'SRBASERIGHT', 'SRRMSB', 'SRRMSA', 'ORTA', 'ORTAERR', 'ORMIDOFFSET', 'ORS2N', 'ORFLAG', 'ORBRMS', 
            # 'ORSLOPE', 'ORBASELEFT', 'ORBASERIGHT', 'ORRMSB', 'ORRMSA', 'ORPC', 'CORTA', 'CORTAERR', 'SLTAFERR', 
            # 'NLTAFERR', 'OLTAFERR', 'OLPSS', 'OLPSSERR', 'OLAPPEFF', 'SRTAFERR', 'NRTAFERR', 'ORTAFERR', 'ORPSS',
            #  'ORPSSERR', 'ORAPPEFF', 'time', 'OLPSSFERR', 'ORPSSFERR', 'TSYS1FERR', 'TSYS2FERR', 'OLPCs', 
            # 'COLTAs', 'COLTAERRs', 'OLPCn', 'COLTAn', 'COLTAERRn', 'ORPCs', 'CORTAs', 'CORTAERRs', 'ORPCn', 
            # 'CORTAn', 'CORTAERRn', 'SLCP', 'SLCPERR', 'SRCP', 'SRCPERR', 'STOT', 'STOTERR']
            ta=[]
            del_ta=[]

            POSITION=['S','N','O']
            
            for l in POLS:
                for p in POSITION:
                    # print(f'{p}{l}')
                    # ta.append(f'{p}{l}TA')
                    # ta.append(f'{p}{l}TAERR')

                    del_ta.append(f'{p}{l}TA')
                    del_ta.append(f'{p}{l}TAERR')
                    del_ta.append(f'{p}{l}S2N')
                    del_ta.append(f'{p}{l}FLAG')
                    del_ta.append(f'{p}{l}BRMS')
                    del_ta.append(f'{p}{l}SLOPE')
                    del_ta.append(f'{p}{l}BASELEFT')
                    del_ta.append(f'{p}{l}BASERIGHT')
                    del_ta.append(f'{p}{l}MIDOFFSET')
                    del_ta.append(f'{p}{l}RMSB')
                    del_ta.append(f'{p}{l}RMSA')    

                    if p=='O':
                        del_ta.append(f'{p}{l}PC')
                        del_ta.append(f'C{p}{l}TA')
                        del_ta.append(f'C{p}{l}TAERR')
                        del_ta.append(f'{p}{l}PSS')
                        del_ta.append(f'{p}{l}PSSERR')
                        del_ta.append(f'{p}{l}APPEFF')

                for c in del_ta:
                    try:
                        self.df.at[pos, c] = np.nan
                    except ValueError:
                        self.df.at[pos, c] = 0.0
                        print(f"Warning: Setting df[{c}] to 0.0 instead of NaN")
                                
                # print(ta,'\n') 
                print('\n',del_ta,'\n') 
                del_ta=[]
                ta=[]

            # sys.exit()
            print(f'\nUpdating table "{self.table}" in database "{self.dbFile}"\n')

            cnx = sqlite3.connect(self.dbFile)
            self.df.to_sql(self.table,cnx,if_exists='replace',index=False)
            cnx.close()
            pass

        elif beam == "06.0D" or beam=="03.5D":
            #['id', 'FILENAME', 'FILEPATH', 'CURDATETIME', 'MJD', 'OBSDATE', 
            # 'OBSTIME', 'OBSDATETIME', 'FRONTEND', 'HDULENGTH', 'OBJECT', 'SRC', 
            # 'OBSERVER', 'OBSLOCAL', 'OBSNAME', 'PROJNAME', 'PROPOSAL', 
            # 'TELESCOP', 'UPGRADE', 'CENTFREQ', 'BANDWDTH', 'LOGFREQ', 
            # 'BEAMTYPE', 'HPBW', 'FNBW', 'SNBW', 'FEEDTYPE', 'LONGITUD', 
            # 'LATITUDE', 'COORDSYS', 'EQUINOX', 'RADECSYS', 'FOCUS', 'TILT', 
            # 'TAMBIENT', 'PRESSURE', 'HUMIDITY', 'WINDSPD', 'SCANDIR', 'POINTING',
            #  'BMOFFHA', 'BMOFFDEC', 'HABMSEP', 'DICHROIC', 'PHASECAL', 'NOMTSYS',
            #  'SCANDIST', 'SCANTIME', 'INSTRUME', 'INSTFLAG', 'HZPERK1', 
            # 'HZKERR1', 'HZPERK2', 'HZKERR2', 'TCAL1', 'TCAL2', 'TSYS1', 
            # 'TSYSERR1', 'TSYS2', 'TSYSERR2', 'ELEVATION', 'ZA', 'HA', 'PWV', 
            # 'SVP', 'AVP', 'DPT', 'WVD', 'SEC_Z', 'X_Z', 'DRY_ATMOS_TRANSMISSION',
            #  'ZENITH_TAU_AT_1400M', 'ABSORPTION_AT_ZENITH', 'ANLTA', 'ANLTAERR', 
            # 'ANLMIDOFFSET', 'ANLS2N', 'BNLTA', 'BNLTAERR', 'BNLMIDOFFSET', 
            # 'BNLS2N', 'NLFLAG', 'NLBRMS', 'NLSLOPE', 'ANLBASELOCS', 
            # 'BNLBASELOCS', 'NLRMSB', 'NLRMSA', 'ASLTA', 'ASLTAERR', 
            # 'ASLMIDOFFSET', 'ASLS2N', 'BSLTA', 'BSLTAERR', 'BSLMIDOFFSET', 'BSLS2N', 'SLFLAG', 'SLBRMS', 'SLSLOPE', 'ASLBASELOCS', 'BSLBASELOCS', 'SLRMSB', 'SLRMSA', 'AOLTA', 'AOLTAERR', 'AOLMIDOFFSET', 'AOLS2N', 'BOLTA', 'BOLTAERR', 'BOLMIDOFFSET', 'BOLS2N', 'OLFLAG', 'OLBRMS', 'OLSLOPE', 'AOLBASELOCS', 'BOLBASELOCS', 'OLRMSB', 'OLRMSA', 'AOLPC', 'ACOLTA', 'ACOLTAERR', 'BOLPC', 'BCOLTA', 'BCOLTAERR', 'ANRTA', 'ANRTAERR', 'ANRMIDOFFSET', 'ANRS2N', 'BNRTA', 'BNRTAERR', 'BNRMIDOFFSET', 'BNRS2N', 'NRFLAG', 'NRBRMS', 'NRSLOPE', 'ANRBASELOCS', 'BNRBASELOCS', 'NRRMSB', 'NRRMSA', 'ASRTA', 'ASRTAERR', 'ASRMIDOFFSET', 'ASRS2N', 'BSRTA', 'BSRTAERR', 'BSRMIDOFFSET', 'BSRS2N', 'SRFLAG', 'SRBRMS', 'SRSLOPE', 'ASRBASELOCS', 'BSRBASELOCS', 'SRRMSB', 'SRRMSA', 'AORTA', 'AORTAERR', 'AORMIDOFFSET', 'AORS2N', 'BORTA', 'BORTAERR', 'BORMIDOFFSET', 'BORS2N', 'ORFLAG', 'ORBRMS', 'ORSLOPE', 'AORBASELOCS', 'BORBASELOCS', 'ORRMSB', 'ORRMSA', 'AORPC', 'ACORTA', 'ACORTAERR', 'BORPC', 'BCORTA', 'BCORTAERR', 'time', 'FLUX', 'AOLPSS', 'AOLPSSERR', 'CAOLTA', 'CAOLTAERR', 'AOLAPPEFF', 'ASLTAFERR', 'ANLTAFERR', 'AOLTAFERR', 'AOLPSSFERR', 'AORPSS', 'AORPSSERR', 'CAORTA', 'CAORTAERR', 'AORAPPEFF', 'ASRTAFERR', 'ANRTAFERR', 'AORTAFERR', 'AORPSSFERR', 'TSYS1FERR', 'TSYS2FERR', 'BOLPSS', 'BOLPSSERR', 'CBOLTA', 'CBOLTAERR', 'BOLAPPEFF', 'BSLTAFERR', 'BNLTAFERR', 'BOLTAFERR', 'BOLPSSFERR', 'BORPSS', 'BORPSSERR', 'CBORTA', 'CBORTAERR', 'BORAPPEFF', 'BSRTAFERR', 'BNRTAFERR', 'BORTAFERR', 'BORPSSFERR', 'AOLPCs', 'CACOLTAs', 'CACOLTAERRs', 'AOLPCn', 'CACOLTAn', 'ACOLTAERRn', 'AORPCs', 'CACORTAs', 'CACORTAERRs', 'AORPCn', 'CACORTAn', 'ACORTAERRn', 'BOLPCs', 'CBCOLTAs', 'CBCOLTAERRs', 'BOLPCn', 'CBCOLTAn', 'BCOLTAERRn', 'BORPCs', 'CBCORTAs', 'CBCORTAERRs', 'BORPCn', 'CBCORTAn', 'BCORTAERRn']
        
            ta=[]
            del_ta=[]

            POSITION=['S','N','O']
            BEAMS=['A','B']
            
            for l in POLS:
                if l=='L':
                    del_ta.append(f'TSYS1')
                    del_ta.append(f'TSYSERR1')
                else:
                    del_ta.append(f'TSYS2')
                    del_ta.append(f'TSYSERR2')
                for b in BEAMS:
                    for p in POSITION:
                        # print(f'{p}{l}')
                        # ta.append(f'{p}{l}TA')
                        # ta.append(f'{p}{l}TAERR')

                        del_ta.append(f'{b}{p}{l}TA')
                        del_ta.append(f'{b}{p}{l}TAERR')
                        del_ta.append(f'{b}{p}{l}S2N')
                        del_ta.append(f'{b}{p}{l}FLAG')
                        del_ta.append(f'{b}{p}{l}BRMS')
                        del_ta.append(f'{b}{p}{l}SLOPE')
                        del_ta.append(f'{b}{p}{l}BASELEFT')
                        del_ta.append(f'{b}{p}{l}BASERIGHT')
                        del_ta.append(f'{b}{p}{l}MIDOFFSET')
                        del_ta.append(f'{b}{p}{l}RMSB')
                        del_ta.append(f'{b}{p}{l}RMSA')    

                        if p=='O':
                            del_ta.append(f'{b}{p}{l}PC')
                            del_ta.append(f'{b}C{p}{l}TA')
                            del_ta.append(f'{b}C{p}{l}TAERR')
                            del_ta.append(f'{b}{p}{l}PSS')
                            del_ta.append(f'{b}{p}{l}PSSERR')
                            del_ta.append(f'{b}{p}{l}APPEFF')

                    for c in del_ta:
                        try:
                            self.df.at[pos, c] = np.nan
                        except ValueError:
                            self.df.at[pos, c] = 0.0
                            print(f"Warning: Setting df[{c}] to 0.0 instead of NaN")
                                    
                    # print(ta,'\n') 
                    print('\n',del_ta,'\n') 
                    del_ta=[]
                    ta=[]

            # sys.exit()
            print(f'\nUpdating table "{self.table}" in database "{self.dbFile}"\n')

            cnx = sqlite3.connect(self.dbFile)
            self.df.to_sql(self.table,cnx,if_exists='replace',index=False)
            cnx.close()
            pass

        else:
            print(f'Invalid beam: {beam}')
            sys.exit()

        # Clear the plot and re-plot the updated data
        self.canvas.clear_figure()
        self.plot_cols(self.canvas.xlab, self.canvas.ylab)

 
    def _connect_data_operations(self):
        """Connect signals for data manipulation operations."""
        self.time_ui.BtnFilter.clicked.connect(self.filter_timeseries_data)
        # self.time_ui.BtnFit.clicked.connect(self.fit_timeseries)
        # self.time_ui.BtnReset.clicked.connect(self.reset_timeseries)
        pass

    def _connect_database_operations(self):
        """Connect signals for database-related operations."""
        self.time_ui.BtnRefreshDB.clicked.connect(self.refresh_db)  # Disabled for now
        # self.time_ui.BtnSaveDB.clicked.connect(self.save_time_db)
        pass

    def refresh_db(self):
        print('Updating table ',self.table)
        self._load_database_tables(self.table)
        # # recalculate corrected ta
        # self.update_db()

        # Clear the plot and re-plot the updated data
        self.canvas.clear_figure()
        # self.canvas.clear_figure()
        self.plot_cols(self.canvas.xlab, self.canvas.ylab)

    

    def filter_timeseries_data(self):
        print('\n***** Running filter_timeseries_data\n')
        # Get filter text and value from UI
        filter_text = self.time_ui.comboBoxFilters.currentText()
        filter_value = self.time_ui.EdtFilter.text()

        if filter_text == "Type":
            print("Please select a filter type")
        else:
            # Handle comparison filters (>, >=, <, <=)
            if filter_text in (">", ">=", "<", "<="):
                try:
                    cut_value = float(filter_value)
                except ValueError:
                    print(f"{filter_value} is an invalid entry for filter {filter_text}")
                    cut_value = None

                if cut_value is not None:
                    print(f"Filtering data with {filter_text} {cut_value}")

                    # # Check if data is plotted
                    # if not self.canvas.has_data():
                    #     print("You need to plot the data first")
                    #     return

                    # x, y = self.canvas.get_data()
                    x_col = self.time_ui.comboBoxColsX.currentText()
                    y_col = self.time_ui.comboBoxColsY.currentText()


                    # Apply filter based on operator
                    y=self.df[y_col]
                    if filter_text == ">":
                        filtered_indices = np.where(y > cut_value)[0]
                    elif filter_text == ">=":
                        filtered_indices = np.where(y >= cut_value)[0]
                    elif filter_text == "<":
                        filtered_indices = np.where(y < cut_value)[0]
                    elif filter_text == "<=":
                        filtered_indices = np.where(y <= cut_value)[0]
                    else:
                        print("Invalid filter operator detected")
                        return

                    # Check if any data remains after filtering
                    if len(filtered_indices) > 0:
                        print(f"Viewing rows at indices: {filtered_indices}")

                        ls = self.df.index[filtered_indices]
                        print(ls)

                        # conditions
                        cond=self.df[ls]

                        # self.df = self.df.drop(self.df.index[filtered_indices])
                        # self.deleted.extend(filtered_indices)
                        # print(f"Deleted rows: {self.deleted}")

                        # # Update plot with filtered data
                        # self.canvas.plot_fig(
                        #     self.df[x_col],
                        #     self.df[y_col],
                        #     x_col,
                        #     y_col,
                        #     data=self.df,
                        #     title=f"Plot of {self.df['SRC'].iloc[-1]} - {x_col} vs {y_col}",
                        # )
                    else:
                        print(f"No values found for {filter_text} {cut_value}")

            # Handle unsupported filter types
            elif filter_text == "rms cuts":
                print("RMS cuts not implemented yet")
            elif filter_text == "binning":
                print("Binning not implemented yet")



    def _prep_data(self):
        """Process and clean the main dataframe."""

        # Sort and process dates
        self.df.sort_values('FILENAME', inplace=True)
        # self.df['OBSDATE'] = self.df.apply(
        #     lambda row: self.parse_time(row['OBSDATE']), 
        #     axis=1
        # )

        # --- Parse observation dates
        self.df = parse_observation_dates(self.df)

        # Add source name to the DataFrame
        self.df['FILES'] = self.df['FILENAME'].str[:18]
        # self.df['OBJECT'] = source_name
        
        self.df["OBSDATE"] = pd.to_datetime(self.df["OBSDATE"]).dt.date
        self.df["OBSDATE"] = pd.to_datetime(self.df["OBSDATE"], format="%Y-%m-%d")
        
        errCols=[col for col in (self.df.columns) if 'ERR' in col]
        for col in errCols:
            self.df[col] = self.df.apply(lambda row: self.make_positive(row[col]), axis=1)

    def make_positive(self, val):
        """Returns the absolute value of the input value.

        Args:
            val: The input value.

        Returns:
            The absolute value of the input, or 0.0 if the input is not a number.
        """

        # print('\n***** Running make_positive\n')
        try:
            return abs(val)
        except TypeError as e:
            msg_wrapper('debug',self.log.debug,f"Error: Cannot calculate absolute value of {val} due to type mismatch. {e}\n")
            return 0.0
        except ValueError as e:
            msg_wrapper('debug',self.log.debug,f"Error: Invalid input value {val}. {e}\n")
            return 0.0
        except Exception as e:
            msg_wrapper('debug',self.log.debug,f"An unexpected error occurred: {e}\n")
            return 0.0

    def _update_ui_components(self):
        """Update UI components with loaded data."""
        print(f"Working with Tables: {self.tables}")
        self.time_ui.comboBoxTables.clear()
        self.time_ui.comboBoxTables.clear()
        self.time_ui.comboBoxTables.addItems(self.tables)
        print('Cleared comboBoxTables ->  _update_ui_components')

    def parse_time(self,timeCol):
        """
        Parses the time column and returns only the date part.

        Args:
            timeCol (str): The time column to parse"""
        
        # print('\n***** Running parse_time\n')
        if 'T' in timeCol:
            return timeCol.split('T')[0]
        else:
            return timeCol.split(' ')[0]

    def plot_cols(self, xcol="", ycol="", yerr=""):
        """Plot selected columns from the database with optional error bars.
        
        Args:
            xcol (str): Column name for x-axis data. If empty, uses current UI selection.
            ycol (str): Column name for y-axis data. If empty, uses current UI selection.
            yerr (str): Column name for error data. If empty or "None", no error bars are shown.
        """
        print('\n***** Running plot_cols\n')

        

        # Get selected table from UI
        self.table = self.time_ui.comboBoxTables.currentText()
        self._load_database_tables(self.table)

         # Handle case where no table is selected
        if not self.table:
            print("Please select a table")
            self._update_ui_components()

        # Get column names from UI or default values
        xcol = xcol if xcol else self.time_ui.comboBoxColsX.currentText()
        ycol = ycol if ycol else self.time_ui.comboBoxColsY.currentText()
        yerr = yerr if yerr else self.time_ui.comboBoxColsYerr.currentText()

        print(f"\nPlotting {xcol} vs {ycol} in table {self.table}")

        try:
            self.df[xcol]=self.df[xcol].astype(float)
        except:
            pass

        if xcol!='OBSDATE':
            self.df[xcol].fillna(value=0, inplace=True)
            self.df[xcol]=self.df[xcol].replace(np.nan, 0.0)
        try:
            self.df[ycol]=self.df[ycol].astype(float)
        except:
            pass

        # 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value)
        # self.df[ycol].fillna(value=0, inplace=True)

        self.df.fillna({ycol:0}, inplace=True)
        self.df[ycol]=self.df[ycol].replace(np.nan, 0.0)

        # sometimes xx-axis is obsdate so need to account for that
        try:
            xvalues=self.df[xcol].astype(float)
        except:
            xvalues=self.df[xcol]

        yvalues=self.df[ycol].astype(float)
        # yvalues.fillna(value=0, inplace=True)
        yvalues=yvalues.replace(0,np.nan)

        isNotNone = str(yerr)=='None'
        # print(isNotNone)

        if isNotNone == False: 
            self.df[yerr] = self.df.apply(lambda row: self.make_positive(row[yerr]), axis=1)
            # self.df[yerr].fillna(value=0, inplace=True)
            self.df.fillna({yerr: 0}, inplace=True)

            self.df[yerr]=self.df[yerr].astype(float)
            self.df[yerr]=self.df[yerr].replace(np.nan, 0.0)
            yerrvalues=self.df[yerr].astype(float)
            self.canvas.plot_fig(xvalues, yvalues, xcol, ycol, data=self.df, yerr=yerrvalues)
        else:
            self.canvas.plot_fig(xvalues, yvalues, xcol, ycol, data=self.df)
            # print('what')

    def view_zoomed_area(self):

        xlim,ylim=self.canvas.onzoom()

        xCol=self.time_ui.comboBoxColsX.currentText()
        yCol=self.time_ui.comboBoxColsY.currentText()

        print('\n',xCol,yCol)

        if xCol=='OBSDATE':
            xmin = str(mdates.num2date(xlim[0]).date())
            xmax = str(mdates.num2date(xlim[1]).date())
            xmin=datetime.strptime(xmin, '%Y-%m-%d')
            xmax=datetime.strptime(xmax, '%Y-%m-%d')
        else:
            xmin = xlim[0]
            xmax = xlim[1]
        
        ymin = ylim[0]
        ymax = ylim[1]

        # print(xmin,xmax)
        print(f"\nZoomed: ymin={ymin:.3f}, ymax={ymax:.3f}")
        print(f"Zoomed: xmin={xmin}, xmax={xmax}")

        # conditions
        cond1=(self.df[xCol]>=xmin) & (self.df[xCol]<=xmax)
        cond2=(self.df[yCol]>=ymin) & (self.df[yCol]<=ymax)

        # get data based on zoomed area
        df=self.df[cond1&cond2]
   
        # # src info
        srcname=df['SRC'].iloc[0]
        print(srcname)
        print(df['SRC'])

        
        freq = int(df['CENTFREQ'].iloc[0])

        print(f'\nPlotting data for {srcname} at freq: {freq} MHz')

        # # Get plot paths
        # image_dir = f"plots/{srcname}/{freq}"
        image_dir=os.path.join(os.path.abspath('.'),'plots')
        image_paths = []

        image_names=sorted(os.listdir(f'{image_dir}/{srcname}/{freq}/'))

        print(f'\nSEARCHING THROUGH: {len(image_names)} IMAGES\n')

        # print(image_names)
        df['FILES'] = df['FILENAME'].str[:18]
        files=sorted(df['FILES'].tolist())
        # filepaths=sorted(df['FILENAME'].tolist())

        # print(df['FILES'].tolist())
        # sys.exit()

        for fl in files:
        #     for pos in ['N','S','O']:
        #         for pol in ['L','R']:
            for flimg in image_names:
                if fl in flimg:
                    image_paths.append(f'{image_dir}/{srcname}/{freq}/{flimg}')
        
        image_paths=sorted(image_paths)
        # print(image_paths)
        
        self.print_basic_stats(df, yCol)

        # file_path = sys.path[0]
        # print(file_path)
        
      
        htmlstart = f"""<!doctype html>
            <head>
            <meta charset = "utf-8" >
            <meta name = "viewport" \
                content = "width=device-width, initial-scale=1" > \
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css" \
                rel="stylesheet" \
                integrity="sha384-4Q6Gf2aSP4eDXB8Miphtr37CMZZQ5oXLH2yaXMJ2w8e2ZtHTl7GptT4jmndRuHDT" \
                crossorigin="anonymous"> \
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js" \
                integrity="sha384-j1CDi7MgGQ12Z7Qab0qlWQ/Qqz24Gc6BM0thvEMVjHnfYGF0rmFCozFSxQBxwHKO" \
                    crossorigin="anonymous"></script> \
            """+"""\
                <style> img {border: 2px solid  #ddd; /* Gray border */
                border-radius: 4px;  /* Rounded border */
                padding: 5px; /* Some padding */
                width: 400px; /* Set a small width */}/* Add a hover effect (blue shadow) */
                img:hover {box-shadow: 0 0 2px 1px rgba(0, 140, 186, 0.5);}
                .card { width: 18rem; margin: 0.5rem; }
                
                </style> 
            """+f"""
            <title>Plots</title>
            </head>
            <body>
            <div class="container-fluid">
                <div class="row">
                <hr>
                    <h4> Plots of obs '{srcname}' at {freq} MHz </h4>


            """    
                                                                     
        #(MJD {data['MJD']:.1f} or {observation_date}) for {source_name} at {central_frequency} MHz </h4>
        html_mid = ""

        # GET ALL COLS NOT MATCHING
        # nonMatchingCols = self.select_non_matching_fields(df.columns)
        

        # if yCol in nonMatchingCols:
        #     print('yCol in Non-matchiing cols: ',nonMatchingCols)
        # else:

        data=[]
        for p in image_paths:
                
            base, ext = os.path.splitext(p) # Remove the extension
            parts = base.split('_') # Split by underscore
                
            if parts[-2].startswith('H'):
                start=parts[-2][-1]+parts[-1][0]
            else:
                start=parts[-2][0]+parts[-1][0]

            # print(base, parts)
            # print('start: ',start)
            # sys.exit()

            if yCol.startswith(start):
                # print(p)
                data.append(p)

            elif yCol.startswith(f'A{start}') or yCol.startswith(f'B{start}'):
                data.append(p)

        data=sorted(data)

        self.zoomed_paths=sorted(data)

        for img_path in data:
            # img_path = os.path.join(image_dir, image_name)
            base, ext = os.path.splitext(img_path)
            img_name=base.split('/')[-1]
            tag="_".join(img_path.split("_")[-2:])
            img_tag, ext = os.path.splitext(tag)
            # print(tag)
            # sys.exit()
            # img_tag = image_name[19:-4]  # Extract image tag from filename

            html_mid += f"""<div class="card">
                <div class="card-body">
                    <h5 class="card-title">{img_tag}</h5>
                    <p class="card-text">{img_name}</p>
                    
                    <a target="_blank" href="{img_path}">
                        <img src="{img_path}" 
                        class="card-img-top" 
                        alt="{img_name}.png goes here">
                    </a>

                    <div class="d-grid gap-2 mt-3">
                        <button class="btn btn-outline-danger btn-sm delete-btn"
                            data-img="{img_path}"
                            data-title="{img_tag}">Delete</button>
                    </div>
                
                </div> 
            </div> 
            
            
            
            
            """

        html_end = f"""</div>
        <script>
      // Change this if you host the API elsewhere
      const DELETE_API = "http://127.0.0.1:5000/delete/{yCol}";

      async function handleDeleteClick(ev) """+"{"+"""
        const btn = ev.currentTarget;
        const card = btn.closest(".card");
        const imagePath = btn.dataset.img;
        const title = btn.dataset.title || "";

        btn.disabled = true;
        btn.textContent = "Deleting...";

        try {
          const resp = await fetch(DELETE_API, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ image_path: imagePath, title })
          });

          if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `HTTP ${resp.status}`);
          }

          // Remove the card from the DOM
          card.remove();
        } catch (err) {
          console.error(err);
          btn.disabled = false;
          btn.textContent = "Delete";
          alert("Failed to delete. Check console / backend logs.");
        }
      }

      // Wire up all delete buttons
      document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.addEventListener("click", handleDeleteClick);
      });
    </script>
        </body></html>"""

        html = htmlstart + html_mid + html_end

                # create the html file
        path = os.path.abspath('temp.html')
        # print(path)
        url = 'file://' + path

        # print(url)
        # sys.exit()
        with open(path, 'w') as f:
            f.write(html)
        webbrowser.open(url)

    def print_basic_stats(self, df, option):
        """Prints basic statistics for the given DataFrame and option."""

        print("\n--- Basic stats ---\n")
        
        try:
            print(f'DATE start: {df["OBSDATE"].iloc[0]}')
            print(f'DATE end: {df["OBSDATE"].iloc[-1]}')
            print(f'MJD start: {df["MJD"].iloc[0]:.1f}')
            print(f'MJD end: {df["MJD"].iloc[-1]:.1f}')
            print(f'3sigma upper limit: {df[option].mean() + (df[option].mean()*df[option].std()):.3f}')
            print(f'3sigma lower limit: {df[option].mean() - (df[option].mean()*df[option].std()):.3f}')
        except:
            print(f'DATE start: {df["OBSDATE"].iloc[0]}')
            print(f'DATE end: {df["OBSDATE"].iloc[-1]}')
            print(f'MJD start: {df["MJD"].iloc[0]:.1f}')
            print(f'MJD end: {df["MJD"].iloc[-1]:.1f}')
        
        print("Min:", df[option].min())
        print("Max:", df[option].max())
        print("Mean:", df[option].mean())
        print("Median:", df[option].median())
        print(f'Len:" {len(df)}')

        print("-" * 20, "\n")

