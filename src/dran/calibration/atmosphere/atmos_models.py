# =========================================================================== #
# File: atmos_models.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import math
from typing import Any, Dict
import numpy as np
from dran.config.constants import DEG_TO_RAD
from dran.calibration.row_accessors import get_float
# =========================================================================== #


def apply_atmospheric_penetration_2p5s(
    row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Apply atmospheric penetration model for 02.5S frontend (nominally 12 GHz band).
    Writes: TAU10, TAU15, TBATMOS10, TBATMOS15, MEAN_ATMOS_CORRECTION
    """
    pwv = get_float(row, "PWV", default=np.nan)
    wvd = get_float(row, "WVD", default=np.nan)
    za_deg = get_float(row, "ZA", default=np.nan)

    if not np.isfinite(pwv) or not np.isfinite(wvd) or not np.isfinite(za_deg):
        row.update(
            {
                "TAU10": np.nan,
                "TAU15": np.nan,
                "TBATMOS10": np.nan,
                "TBATMOS15": np.nan,
                "MEAN_ATMOS_CORRECTION": np.nan,
            }
        )
        return

    try:
        tau10 = 0.0071 + 0.00021 * pwv
        tau15 = (0.055 + 0.004 * wvd) / 4.343
        tbatmos10 = 260.0 * (1.0 - math.exp(-tau10))
        tbatmos15 = 260.0 * (1.0 - math.exp(-tau15))
    except (ValueError, OverflowError):
        tau10, tau15, tbatmos10, tbatmos15 = np.nan, np.nan, np.nan, np.nan

    try:
        za_rad = np.deg2rad(za_deg)
        mean_atm = math.exp((tau15 + tau10) / 2.0 / math.cos(za_rad))
    except (ValueError, ZeroDivisionError, OverflowError):
        mean_atm = np.nan

    params = {
        "TAU10": tau10,
        "TAU15": tau15,
        "TBATMOS10": tbatmos10,
        "TBATMOS15": tbatmos15,
        "MEAN_ATMOS_CORRECTION": mean_atm,
    }
    row.update(params)
    log.debug("02.5S atmosphere derived: %s", params)


def apply_atmospheric_absorption_sb(
    row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Apply simple atmospheric absorption model for high frequency frontends (SB).
    Writes: ATMOSABS
    """
    za_deg = get_float(row, "ZA", default=np.nan)
    if not np.isfinite(za_deg):
        row["ATMOSABS"] = np.nan
        return

    try:
        atmosabs = math.exp(0.005 / math.cos(np.deg2rad(za_deg)))
    except (ValueError, ZeroDivisionError, OverflowError):
        atmosabs = np.nan

    row["ATMOSABS"] = atmosabs
    log.debug("SB atmosphere derived: ATMOSABS=%s", atmosabs)


def apply_atmospheric_penetration_1p3s(
    row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Apply atmospheric penetration model for 01.3S frontend (nominally 22 
    GHz band).
    Writes: TAU221, TAU2223, TBATMOS221, TBATMOS2223
    """
    pwv = get_float(row, "PWV", default=np.nan)
    wvd = get_float(row, "WVD", default=np.nan)

    if not np.isfinite(pwv) or not np.isfinite(wvd):
        row.update({"TAU221": np.nan, "TAU2223": np.nan, 
                    "TBATMOS221": np.nan, "TBATMOS2223": np.nan})
        return

    try:
        tau221 = 0.0140 + 0.00780 * pwv
        tau2223 = (0.110 + 0.048 * wvd) / 4.343
        tbatmos221 = 260.0 * (1.0 - math.exp(-tau221))
        tbatmos2223 = 260.0 * (1.0 - math.exp(-tau2223))
    except (ValueError, OverflowError):
        tau221, tau2223, tbatmos221, tbatmos2223 = (
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        )

    params = {
        "TAU221": tau221,
        "TAU2223": tau2223,
        "TBATMOS221": tbatmos221,
        "TBATMOS2223": tbatmos2223,
    }
    row.update(params)
    log.debug("01.3S atmosphere derived: %s", params)


def apply_atmospheric_absorption_db(
    row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Apply atmospheric absorption model for D frontend.
    Writes: SEC_Z, X_Z, DRY_ATMOS_TRANSMISSION, ZENITH_TAU_AT_1400M, 
    ABSORPTION_AT_ZENITH
    """
    za_deg = get_float(row, "ZA", default=np.nan)
    pwv = get_float(row, "PWV", default=np.nan)

    if not np.isfinite(za_deg) or not np.isfinite(pwv):
        row.update(
            {
                "SEC_Z": np.nan,
                "X_Z": np.nan,
                "DRY_ATMOS_TRANSMISSION": np.nan,
                "ZENITH_TAU_AT_1400M": np.nan,
                "ABSORPTION_AT_ZENITH": np.nan,
            }
        )
        return

    za_rad = np.deg2rad(za_deg)
    dtr = 0.01745329 #! TODO: where does this number come from??
    
    try:
        sec_z = 1.0 / math.cos(za_rad) # 1.0 / np.cos(za  * dtr)
        x_z = (-0.0045 + 1.00672 * sec_z - 0.002234 * sec_z**2 - 0.0006247 * sec_z**3)
        dry_atmos_transmission = 1.0 / math.exp(0.0069 * (1.0 / math.sin((90.0 - za_deg) * DEG_TO_RAD) - 1.0))
        zenith_tau_at_1400m = 0.00610 + 0.00018 * pwv
        abs_at_zenith = math.exp(zenith_tau_at_1400m * x_z)
    except (ValueError, ZeroDivisionError, OverflowError):
        sec_z, x_z, dry_atmos_transmission, zenith_tau_at_1400m, abs_at_zenith = np.nan, np.nan, np.nan, np.nan, np.nan


    params = {
        "SEC_Z": sec_z,
        "X_Z": x_z,
        "DRY_ATMOS_TRANSMISSION": dry_atmos_transmission,
        "ZENITH_TAU_AT_1400M": zenith_tau_at_1400m,
        "ABSORPTION_AT_ZENITH": abs_at_zenith,
    }
    row.update(params)
    log.debug("db atmosphere derived: %s", params)
