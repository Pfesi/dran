# =========================================================================== #
# File: planet_geometry.py.                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from datetime import datetime
from typing import Any, Dict
import numpy as np
from dran.config.constants import (ARCSEC_TO_RAD, AU_TO_KM, 
                                  JUPITER_MEAN_DIAMETER_KM)
from .ephemeris.jpl_horizons_table import (
    load_jpl_horizons_table)
from dran.calibration.errors import (
    EphemerisDateOutOfRangeError,
    InvalidObservationDateError,
)
# =========================================================================== #


def add_planet_angular_diameter(row: Dict[str, Any], log: logging.Logger
                                ) -> None:
    """
    Add PLANET_ANG_DIAM (arcsec) to row using the packaged Horizons table.

    Requires:
      - DATE as YYYY-MM-DDTHH:MM:SS
    """
    obsdate = str(row.get("DATE", "")).strip()

    try:
        date_key = datetime.strptime(
            obsdate, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%b-%d")
    except ValueError as exc:
        raise InvalidObservationDateError(f"Invalid DATE format: {obsdate}") from exc

    jpl_table = load_jpl_horizons_table(log)

    try:
        result = jpl_table[jpl_table["DATE"] == str(date_key)]
        if result.empty:
            raise KeyError("No matching DATE row found.")
        row["PLANET_ANG_DIAM"] = float(result["ANG-DIAM"].iloc[0])
        log.debug("Planet angular diameter derived: PLANET_ANG_DIAM=%s", row["PLANET_ANG_DIAM"])
    except Exception as exc:
        raise EphemerisDateOutOfRangeError(f"Ephemeris table has no entry for date {date_key}.") from exc


def add_jupiter_distance_au(row: Dict[str, Any], log: logging.Logger
                            ) -> None:
    """
    Add Jupiter distance inferred from angular diameter.

    Requires:
      - PLANET_ANG_DIAM in arcsec

    Adds:
      - PLANET_ANG_DIAM_RAD
      - JUPITER_DIST_AU
    """
    try:
        ang_diam_arcsec = float(row["PLANET_ANG_DIAM"]) # units of arcseconds, see nasa jpl horizons file
        ang_diam_rad = ang_diam_arcsec * ARCSEC_TO_RAD
        jup_distance_km = JUPITER_MEAN_DIAMETER_KM / ang_diam_rad
        jup_distance_au = jup_distance_km / AU_TO_KM
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        ang_diam_rad = np.nan
        jup_distance_au = np.nan

    row["PLANET_ANG_DIAM_RAD"] = ang_diam_rad
    row["JUPITER_DIST_AU"] = jup_distance_au
    log.debug("Jupiter geometry derived: PLANET_ANG_DIAM_RAD=%s JUPITER_DIST_AU=%s", ang_diam_rad, jup_distance_au)
