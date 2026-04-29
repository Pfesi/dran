# =========================================================================== #
# File: resource_utils.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Standard library
# --------------------------------------------------------------------------- #
from typing import Final, Optional
from logging import Logger
import importlib.resources as resources

# Third-party
# --------------------------------------------------------------------------- #
import pandas as pd

# =========================================================================== #
# Constants
# =========================================================================== #

# IMPORTANT:
# This must be a real Python package path (dot notation, not filesystem path)
_PREDEFS_PACKAGE: Final[str] = "dran.calibration.predefs"

_CAL_LIST_FILENAME: Final[str] = "cal_names_list.txt"
_NASA_JPL_FILENAME: Final[str] = "nasa_jpl_data.txt"


# =========================================================================== #
# Helpers
# =========================================================================== #

def _get_resource_path(filename: str) -> resources.abc.Traversable:
    """
    Return a Traversable object pointing to a packaged resource file.

    This works for both:
    - Local filesystem
    - Installed packages (zip-safe)
    """
    return resources.files(_PREDEFS_PACKAGE).joinpath(filename)


# =========================================================================== #
# Public API
# =========================================================================== #

# def get_cal_list() -> pd.DataFrame:
#     """
#     Load calibrator names from packaged resource file.

#     Returns
#     -------
#     pandas.DataFrame
#         DataFrame with a single column 'CALS'.
#     """
#     resource = _get_resource_path(_CAL_LIST_FILENAME)

#     # Convert to real file path when needed by pandas
#     with resources.as_file(resource) as file_path:
#         return pd.read_fwf(file_path, names=["CALS"])


def get_jpl_results(log: Optional[Logger] = None) -> pd.DataFrame:
    """
    Load NASA JPL Horizons ephemeris data.

    Source:
    https://ssd.jpl.nasa.gov/horizons/app.html#/

    Returns
    -------
    pandas.DataFrame
        Columns:
        ['DATE', 'MJD', 'RA', 'DEC', 'ANG-DIAM']
    """
    if log:
        log.debug("Loading NASA JPL Horizons data.")

    resource = _get_resource_path(_NASA_JPL_FILENAME)

    with resources.as_file(resource) as file_path:
        return pd.read_csv(
            file_path,
            delimiter=",",
            skiprows=1,
            names=["DATE", "MJD", "RA", "DEC", "ANG-DIAM"],
        )