
# =========================================================================== #
# File: resource_utils.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Final
from logging import Logger
import importlib.resources as resources
import pandas as pd 
# =========================================================================== #


# ----------------------------------------------------------------------------
# Module-level constants
# ----------------------------------------------------------------------------

_PREDEFS_PACKAGE: Final[str] = "src.predefs"
_CAL_LIST_FILENAME: Final[str] = "cal_names_list.txt"
_NASA_JPL_FILENAME: Final[str] = "nasa_jpl_data.txt"



def get_cal_list() -> pd.DataFrame:
    """
    Return the list of calibrator names from the packaged text file.

    The underlying resource is expected to contain a single column with one
    calibrator name per line.

    Returns
    -------
    pandas.DataFrame
        DataFrame with a single column 'CALS' containing calibrator names.
    """

    with resources.path(_PREDEFS_PACKAGE, _CAL_LIST_FILENAME) as df:
        return pd.read_fwf(df,names=['CALS'])

def get_jpl_results(log: Logger | None = None) -> pd.DataFrame:
    """
    Load NASA JPL Horizons ephemeris results from a packaged CSV file.

    The data are assumed to be generated from:
    https://ssd.jpl.nasa.gov/horizons/app.html#/

    Configuration used:
    - Ephemeris type: Observer Table
    - Target body   : Jupiter
    - Observer      : Geocentric [500]
    - Time span     : 1950 to 2100, step = 1 day

    Parameters
    ----------
    log : logging.Logger, optional
        Logger instance for debug messages. If ``None``, logging is skipped.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns:
        ['DATE', 'MJD', 'RA', 'DEC', 'ANG-DIAM']
    """
    if log:
        log.debug("Loading NASA JPL Horizons data (angular diameter).")

    with resources.path(_PREDEFS_PACKAGE, _NASA_JPL_FILENAME) as df:
        return pd.read_csv(df,delimiter=",", skiprows=1, names=['DATE','MJD','RA','DEC','ANG-DIAM'])
