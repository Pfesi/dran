# =========================================================================== #
# File: baseline_correction.py                                                #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Tuple
import numpy as np
from src.fitting.spline_models import spline_fit_1d
# =========================================================================== #


def fit_polynomial(x: np.ndarray, y: np.ndarray, deg: int
                   ) -> Tuple[np.ndarray, np.ndarray]:
    """Fit a polynomial model to data.
    Returns the polynomial coefficients and the evaluated model values at the 
    input x coordinates.
    """
    coeffs = np.polyfit(x, y, deg)
    model = np.polyval(coeffs, x)
    return coeffs, model


def calc_residual_and_rms(model: np.ndarray, data: np.ndarray
                          ) -> Tuple[np.ndarray, float]:
    """Compute residuals and root-mean-square error between model and data.
    Returns the residual array and the RMS error value.
    """
    res = model - data
    rms = float(np.sqrt(np.nanmean(np.asarray(res, dtype=float) ** 2)))
    return res, rms


def correct_baseline_linear(
    x: np.ndarray,
    y: np.ndarray,
    baseline_indices: np.ndarray,
    log: logging.Logger,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    
    """
    Fits linear drift over baseline indices, subtracts it from y.
    Returns:
        y_corrected, y_corrected_spline, baseline_coeffs, baseline_residual, baseline_rms
    """
    bx = x[baseline_indices]
    by = y[baseline_indices]

    coeffs, model = fit_polynomial(bx, by, deg=1)
    res, rms = calc_residual_and_rms(model, by)

    drift = np.poly1d(coeffs)
    y_corrected = y - drift(x)
    y_corr_spline = spline_fit_1d(y_corrected, log=log)

    return y_corrected, y_corr_spline, coeffs, res, rms