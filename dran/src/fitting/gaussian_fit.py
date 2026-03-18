# =========================================================================== #
# File: gaussian_fit.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Optional, Tuple
import numpy as np
from scipy.optimize import curve_fit, OptimizeWarning
import warnings
# =========================================================================== #


def gauss_plus_linear_baseline(x: np.ndarray, amp: float, mu: float, hpbw: float, a: float, c: float) -> np.ndarray:
    """
    Gaussian main lobe with a first-order baseline: amp*exp(...) + a*x + c

    Notes:
    - HPBW is converted to sigma via sigma = HPBW / (2*sqrt(2*ln(2))).
    """
    sigma = hpbw / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    return amp * np.exp(-((x - mu) ** 2) / (2.0 * sigma**2)) + a * x + c

def fit_gaussian_test(
    x: np.ndarray,
    y: np.ndarray,
    p0: list[float],
    log: logging.Logger,
) -> Tuple[np.ndarray, np.ndarray, Optional[int]]:
    """
    Quick Gaussian fit used as a quality gate.

    Returns:
        (coeffs, model, flag)
        flag is None on success, else an int.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OptimizeWarning)
            coeffs, _cov = curve_fit(
                gauss_plus_linear_baseline,
                x,
                y,
                p0,
                maxfev=2000,
            )
        model = gauss_plus_linear_baseline(x, *coeffs)
        log.debug("Gaussian test fit succeeded. coeffs=%s", coeffs)
        return coeffs, model, None
    except Exception as exc:
        log.debug("Gaussian test fit failed: %s", exc)
        return np.array([]), np.array([]), 3
