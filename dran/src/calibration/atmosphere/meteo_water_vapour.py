# =========================================================================== #
# File: meteo_water_vapour.py                                                 #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import math
from typing import Any, Dict
import numpy as np
from src.calibration.row_accessors import get_float
# =========================================================================== #


def add_water_vapour_fields(
    row: Dict[str, Any],
    log: logging.Logger,
) -> Dict[str, Any]:
    """
    Add water-vapour-related derived fields to row.

    Expected inputs:
      - HUMIDITY: relative humidity in percent
      - TAMBIENT: ambient temperature in Kelvin
      - PRESSURE: surface pressure in hPa (optional, currently unused)

    Adds:
      - PWV: precipitable water vapour (mm)
      - SVP: saturation vapour pressure (kPa)
      - AVP: actual vapour pressure (kPa)
      - DPT: dew-point temperature (C, formula output used as-is)
      - WVD: water vapour density (g/m^3)
    """
    rh_percent = get_float(row, "HUMIDITY", default=np.nan)
    temp_k = get_float(row, "TAMBIENT", default=np.nan)
    _pressure_hpa = get_float(row, "PRESSURE", default=np.nan)

    log.debug("Water vapour inputs: HUMIDITY=%s TAMBIENT=%s PRESSURE=%s", rh_percent, temp_k, _pressure_hpa)
   
    if not np.isfinite(rh_percent) or not np.isfinite(temp_k) or temp_k <= 0:
        row.update({"PWV": np.nan, "SVP": np.nan, "AVP": np.nan, "DPT": np.nan, "WVD": np.nan})
        return row

    try:
        pwv_mm = max(0.0, 4.39 * rh_percent / 100.0 / temp_k * math.exp(26.23 - 5416.0 / temp_k))
        svp_kpa = 0.611 * math.exp(17.27 * (temp_k - 273.13) / (temp_k - 273.13 + 237.3))
        avp_kpa = svp_kpa * rh_percent / 100.0
        dpt_k = (116.9 + 237.3 * math.log(avp_kpa)) / (16.78 - math.log(avp_kpa)) if avp_kpa > 0 else np.nan
        wvd_g_m3 = max(0.0, 2164.0 * avp_kpa / temp_k)
    except (ValueError, ZeroDivisionError, OverflowError):
        pwv_mm, svp_kpa, avp_kpa, dpt_k, wvd_g_m3 = np.nan, np.nan, np.nan, np.nan, np.nan

    params = {"PWV": pwv_mm, "SVP": svp_kpa, "AVP": avp_kpa, "DPT": dpt_k, "WVD": wvd_g_m3}
    row.update(params)
    log.debug("Water vapour derived: %s", params)

    return row
