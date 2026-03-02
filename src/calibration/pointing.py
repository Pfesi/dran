# =========================================================================== #
# File: pointing.py                                                           #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# ---------------------------------------------------------------------------- #
from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np
import logging
# =|========================================================================= #


@dataclass(frozen=True, slots=True)
class PointingGainResult:
    pc: Optional[float]
    ta_corr: Optional[float]
    ta_corr_err: Optional[float]
    reason: str


def _safe_log_abs(x: float) -> Optional[float]:
    """Compute the natural logarithm of the absolute value safely.
    Returns None for null, non-finite, or non-positive inputs.
    """

    if x is None:
        return None
    x = float(x)
    
    if not np.isfinite(x):
        return None
    ax = abs(x)
    
    if ax <= 0.0:
        return None
    
    return float(np.log(ax))


def calc_pointing_correction(hps_ta, hps_err, 
                            hpn_ta, hpn_err, 
                            on_ta,on_err, 
                            data, 
                            missing_side):
    """Compute pointing correction factor and corrected antenna temperature 
    with propagated uncertainty.
    Uses safe log transforms of scan peak temperatures to derive a pointing 
    correction based on which beam side is missing, then applies the 
    correction to on-source temperature and propagates errors via partial 
    derivatives.
    """

    # Derivatives of pc w.r.t Ta1 and Ta2
    # pc = exp( (d^2)/denom ), d = ln|Ta1| - ln|Ta2| (+/- ln2)
    # d(pc)/d(Ta1) = pc * (2*d/denom) * (1/Ta1)
    # d(pc)/d(Ta2) = pc * (2*d/denom) * (-1/Ta2)

    lnS = _safe_log_abs(hps_ta)
    lnN = _safe_log_abs(hpn_ta)
    lnO = _safe_log_abs(on_ta)

    if missing_side == "n":
        d = (lnS-lnO) + float(np.log(2.0))
        denom = 4.0 * float(np.log(2.0))
        expo = (d**2) / denom
        pc = float(np.exp(expo))

        # calculate the derivatives
        hps_der = pc * 2.0 * expo * (1.0/hps_ta)
        on_der = pc * 2.0 * expo * (-1.0/on_ta)
        err_ta_corrected = np.sqrt((hps_err**2)*(hps_der**2) + (on_err**2)*(on_der**2))

    elif missing_side == "s":
        d = (lnO-lnN) - float(np.log(2.0))
        denom = 4.0 * float(np.log(2.0))
        expo = (d**2) / denom
        pc = float(np.exp(expo))

        # calculate the derivatives
        on_der = pc * 2.0 * expo * (1.0/on_ta)
        hpn_der = pc * 2.0 * expo * (-1.0/hpn_ta)
        err_ta_corrected = np.sqrt((on_err**2)*(on_der**2) + (hpn_err**2)*(hpn_der**2))

    else:
        d=lnS-lnN
        denom = 16.0 * float(np.log(2.0))
        expo = (d**2) / denom
        pc = float(np.exp(expo))

        # calculate the derivatives
        hps_der = pc * 2.0 * expo * (1.0/hps_ta)
        hpn_der = pc * 2.0 * expo * (-1.0/hpn_ta)
        err_ta_corrected = np.sqrt((hps_err**2)*(hps_der**2) + (hpn_err**2)*(hpn_der**2))

    ta_corrected = calc_tcorr(on_ta, pc, data)

    return pc, ta_corrected, err_ta_corrected


def calc_tcorr(Ta, pc, data):
    """
        Calculate the antenna temperature correction for high frequencies.

        Args:
            Ta - the on scan antenna temperature 
            pc - the pointing correction 
            data - the dictionary containing all the drift scan parameters

        Returns:
            corrTa - the corrected antenna temperature
    """

    Ta= float(Ta)
    pc=float(pc)
    if data["FRONTEND"] == "01.3S":
        if data["OBJECT"].upper() == "JUPITER":
                # Only applying a size correction factor and atmospheric correction to Jupiter
                # See van Zyl (2023) - in Prep
                abs=float(data["ATMOS_ABSORPTION_CORR"])
                scf=float( data["SIZE_CORRECTION_FACTOR"])
                corrTa = Ta * pc * abs * scf
                return corrTa
        else:
            # do we also apply a atmospheric correcttion factor directly to the target source ?
            # find out, for now I'm not applyin it
            # tests this ASAP
            corrTa = Ta * pc #* data["ATMOS_ABSORPTION_CORR"]
            return corrTa
    else:
        corrTa = Ta*pc
        return corrTa
    

def pointing_gain_from_halfpower(
    hpn_ta: float,
    hpn_err: float,
    on_ta: float,
    on_err: float,
    hps_ta: float,
    hps_err: float,
    data:Dict,
    log: logging.Logger,
    missing_side: Optional[str],
    
) -> PointingGainResult:
    """
    Compute multiplicative pointing gain factor pc and 1-sigma uncertainty pc_err.

    missing_side:
      None  -> both half-power points available (south and north)
      "n"   -> missing north half-power, use (HPS, ON) form in caller if needed
      "s"   -> missing south half-power, use (ON, HPN) form in caller if needed

    This function expects the two temperatures supplied belong to the two
    half-power points used in the same equation.
    """


    hps_ta = float(abs(hps_ta)) if np.isfinite(hps_ta) else float("nan")
    hps_err = float(abs(hps_err)) if np.isfinite(hps_err) else float("nan")
    hpn_ta = float(abs(hpn_ta)) if np.isfinite(hpn_ta) else float("nan")
    hpn_err = float(abs(hpn_err)) if np.isfinite(hpn_err) else float("nan")
    on_ta = float(abs(on_ta)) if np.isfinite(on_ta) else float("nan")
    on_err = float(abs(on_err)) if np.isfinite(on_err) else float("nan")

    pc, ta, ta_corr = calc_pointing_correction(hps_ta, hps_err, 
                                               hpn_ta, hpn_err, 
                                               on_ta,on_err, 
                                               data,
                                               missing_side)

    return PointingGainResult(pc=pc, 
                              ta_corr=ta, 
                              ta_corr_err=ta_corr, 
                              reason='ok')
