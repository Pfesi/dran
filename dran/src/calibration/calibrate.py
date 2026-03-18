# =========================================================================== #
# File: calibrate.py                                                          #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# ---------------------------------------------------------------------------- #
from typing import Any, Mapping
import numpy as np

from .pointing import pointing_gain_from_halfpower, PointingGainResult
import logging
# =|========================================================================= #


def calibrate_pointing_corrected_ta(
    hps_ta: float, hps_err: float,
    hpn_ta: float, hpn_err: float,
    on_ta: float, on_err: float,
    log: logging.Logger,
    row: Mapping[str, Any]
) -> PointingGainResult:
    
    # Decide which pointing equation to use, preserving your old behavior
    if on_ta is None or not np.isfinite(float(on_ta)) or float(on_ta) == 0.0:
        return PointingGainResult(pc=None, ta_corr=None, ta_corr_err=None, reason='Failed to estimate pointing')
    

    hps_ok = hps_ta is not None and np.isfinite(float(hps_ta)) and float(hps_ta) != 0.0
    hpn_ok = hpn_ta is not None and np.isfinite(float(hpn_ta)) and float(hpn_ta) != 0.0

    
    if hps_ok and hpn_ok:
        pc_res = pointing_gain_from_halfpower(hpn_ta, hpn_err, 
                                              on_ta, on_err,  
                                              hps_ta, hps_err,
                                              row, log,
                                              missing_side=None,
                                            #   log
                                              )
    elif hps_ok and not hpn_ok:
        # missing north, your original used (HPS, ON) with +ln2 form
        pc_res = pointing_gain_from_halfpower(hpn_ta, hpn_err, 
                                              on_ta, on_err,  
                                              hps_ta, hps_err,
                                              row,log,
                                              missing_side="n",
                                            #   log
                                              )
    elif hpn_ok and not hps_ok:
        # missing south, your original used (ON, HPN) with -ln2 form
        pc_res = pointing_gain_from_halfpower(hpn_ta, hpn_err, 
                                              on_ta, on_err,  
                                              hps_ta, hps_err,
                                              row,log,
                                              missing_side="s",
                                            #   log
                                              )
    else:
        return PointingGainResult(pc=None, ta_corr=None, ta_corr_err=None, reason='Failed to estimate pointing')
    
    return pc_res


# def pss_for_row(
#     corr_ta: float,
#     corr_ta_err: float,
#     row: Mapping[str, Any],
# ) -> Tuple[float, float, float]:
#     obj = str(row.get("OBJECT", "") or "").upper()

#     if obj == "JUPITER":
#         flux = float(row.get("TOTAL_PLANET_FLUX_D", float("nan")))
#     else:
#         flux = calibrator_flux_ott_1994(row)

#     res = pss_from_flux_and_ta(flux, corr_ta, corr_ta_err)
#     if not res.ok:
#         return float("nan"), float("nan"), float("nan")

#     return float(res.pss), float(res.pss_err), float(res.aperture_eff)
