# =========================================================================== #
# File: planet_jupiter_calibration.py.                                        #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import math
from typing import Any, Dict
import numpy as np
from dran.calibration.row_accessors import get_float
from dran.calibration.planets.planet_geometry import (
    add_jupiter_distance_au, add_planet_angular_diameter)
# =========================================================================== #


def apply_jupiter_atmospheric_calibration(row: Dict[str, Any], 
                                          log: logging.Logger) -> None:
    """
    Apply Jupiter calibration fields for 22 GHz observations.

    This function mutates row in place and assumes TAU221 already exists.
    """
    log.debug("Applying Jupiter atmospheric calibration fields.")

    add_planet_angular_diameter(row, log)
    add_jupiter_distance_au(row, log)


    jupiter_dist_au = get_float(row, "JUPITER_DIST_AU", default=np.nan)
    planet_ang_diam_rad = get_float(row, "PLANET_ANG_DIAM_RAD", default=np.nan)
    cent_freq = get_float(row, "CENTFREQ", default=np.nan)
    za_deg = get_float(row, "ZA", default=np.nan)
    tau221 = get_float(row, "TAU221", default=np.nan)

    if not np.isfinite(jupiter_dist_au) or not np.isfinite(planet_ang_diam_rad) or not np.isfinite(cent_freq):
        log.warning("Jupiter calibration skipped due to missing derived inputs.")
        return

    # TODO: Verify HPBW constant and origin.
    hpbw_arcsec = 0.033 * 3600.0
    adopted_planet_tb = 136.0  # Gibson, Welch, de Pater (2005)

    sync_flux_density = 1.6 * (4.04 / jupiter_dist_au) ** 2

    ang_diam_radius = planet_ang_diam_rad / 2.0
    planet_solid_angle = math.pi * ang_diam_radius**2 * 0.935

    # Flux density terms
    try:
        thermal_flux = 2.0 * 1380.0 * adopted_planet_tb * planet_solid_angle / (300.0 / cent_freq) ** 2
        total_planet_flux_d = sync_flux_density + thermal_flux
        total_planet_flux_d_wmap = 2.0 * 1380.0 * 135.2 * planet_solid_angle / (300.0 / cent_freq) ** 2
    except (ValueError, ZeroDivisionError, OverflowError):
        thermal_flux = np.nan
        total_planet_flux_d = np.nan
        total_planet_flux_d_wmap = np.nan

    # Size correction
    try:
        planet_ang_diam_arcsec = get_float(row, "PLANET_ANG_DIAM", default=np.nan)
        size_factor = (planet_ang_diam_arcsec * math.sqrt(0.935)) / (1.2 * hpbw_arcsec)
        size_correction_factor = (size_factor**2) / (1.0 - math.exp(-size_factor**2))
    except (ValueError, ZeroDivisionError, OverflowError):
        size_factor = np.nan
        size_correction_factor = np.nan

    measured_tcal1 = 71.4
    measured_tcal2 = 70.1

    tcal1 = get_float(row, "TCAL1", default=np.nan)
    tcal2 = get_float(row, "TCAL2", default=np.nan)

    meas_tcal1_corr = (measured_tcal1 / tcal1) if np.isfinite(tcal1) and tcal1 != 0 else np.nan
    meas_tcal2_corr = (measured_tcal2 / tcal2) if np.isfinite(tcal2) and tcal2 != 0 else np.nan

    # Atmospheric absorption correction from tau at source zenith angle
    if np.isfinite(za_deg) and np.isfinite(tau221):
        try:
            za_rad = np.deg2rad(za_deg)
            atm_abs_corr = math.exp(tau221 / math.cos(za_rad))
        except (ValueError, ZeroDivisionError, OverflowError):
            za_rad = np.nan
            atm_abs_corr = np.nan
    else:
        za_rad = np.nan
        atm_abs_corr = np.nan

    jupiter_params = {
        "HPBW_ARCSEC": hpbw_arcsec,
        "ADOPTED_PLANET_TB": adopted_planet_tb,
        "SYNCH_FLUX_DENSITY": sync_flux_density,
        "PLANET_ANG_EQ_RAD": ang_diam_radius,
        "PLANET_SOLID_ANG": planet_solid_angle,
        "THERMAL_PLANET_FLUX_D": thermal_flux,
        "SIZE_FACTOR_IN_BEAM": size_factor,
        "SIZE_CORRECTION_FACTOR": size_correction_factor,
        "MEASURED_TCAL1": measured_tcal1,
        "MEASURED_TCAL2": measured_tcal2,
        "MEAS_TCAL1_CORR_FACTOR": meas_tcal1_corr,
        "MEAS_TCAL2_CORR_FACTOR": meas_tcal2_corr,
        "ZA_RAD": za_rad,
        "TOTAL_PLANET_FLUX_D": total_planet_flux_d,
        "TOTAL_PLANET_FLUX_D_WMAP": total_planet_flux_d_wmap,
        "ATMOS_ABSORPTION_CORR": atm_abs_corr,
    }

    row.update(jupiter_params)
    log.debug("Jupiter calibration derived: %s", jupiter_params)
