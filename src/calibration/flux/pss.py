# =========================================================================== #
# File: pss.py                                                                #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# ---------------------------------------------------------------------------- #
from dataclasses import dataclass
import numpy as np
# =|========================================================================= #


@dataclass(frozen=True, slots=True)
class PssResult:
    pss: float
    pss_err: float
    aperture_eff: float
    ok: bool
    reason: str


def pss_from_flux_and_ta(flux_jy: float, ta_k: float, ta_err: float
                         ) -> PssResult:
    
    """Compute point-source sensitivity and aperture efficiency from flux and 
    antenna temperature.
    Validates inputs, derives PSS from flux and antenna temperature, 
    propagates uncertainty, computes aperture efficiency for a 25.9 m dish, 
    and returns results with a validity flag and reason.
    """
    
    flux_jy = float(flux_jy) if flux_jy is not None else float("nan")
    ta_k = float(ta_k) if ta_k is not None else float("nan")
    ta_err = float(abs(ta_err)) if ta_err is not None else float("nan")

    if not np.isfinite(flux_jy) or flux_jy <= 0.0:
        return PssResult(float("nan"), float("nan"), float("nan"), False, "invalid flux")

    if not np.isfinite(ta_k) or ta_k <= 0.0:
        return PssResult(float("nan"), float("nan"), float("nan"), False, "invalid ta")

    pss = flux_jy / (2.0 * ta_k)

    if np.isfinite(ta_err) and ta_k != 0.0:
        pss_err = float(np.sqrt((ta_err / ta_k) ** 2) * pss)
    else:
        pss_err = float("nan")

    # 25.9 m dish diameter, preserved from your code
    d_m = 25.9
    aperture_eff = 1380.0 / np.pi / (d_m / 2.0) ** 2 / pss

    ok = np.isfinite(pss) and np.isfinite(aperture_eff)
    reason = "ok" if ok else "non-finite result"
    return PssResult(float(pss), float(pss_err), float(aperture_eff), ok, reason)
