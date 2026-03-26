# =========================================================================== #
# File: peak_fitting.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Tuple
import numpy as np
# =========================================================================== #


def peak_window_indices(
    x: np.ndarray,
    y_spline: np.ndarray,
    hfnbw: float,
    cut_fraction: float,
) -> np.ndarray:
    """
    Selects indices within |x| <= hfnbw and spline >= cut_fraction * 
    max(spline).
    """
    max_spline = float(np.max(y_spline)) if y_spline.size else float("nan")
    mask_y = np.abs(x) <= hfnbw
    mask_x = y_spline >= (cut_fraction * max_spline)
    return np.where(mask_x & mask_y)[0]


def fit_quadratic_peak(
    x: np.ndarray,
    y: np.ndarray,
    log: logging.Logger,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Quadratic fit. Returns coeffs, model, rms.
    """
    if x.size < 3:
        log.warning("Quadratic peak fit skipped: need at least 3 points, got %s", x.size)
        return np.array([]), np.array([]), float("nan")

    coeffs = np.polyfit(x, y, 2)
    model = np.polyval(coeffs, x)
    res = np.asarray(model - y, dtype=float)
    rms = float(np.sqrt(np.nanmean(res ** 2)))
    log.debug("Quadratic peak fit: coeffs=%s rms=%s", coeffs, rms)
    return coeffs, model, rms


def calc_residual(model, data):
    """
        Calculate the residual and rms between the model and the data.

        Parameters:
            model (array): 1D array containing the model data
            data (array): 1D array containing the raw data
            log (object): file logging object

        Returns
        -------
        res: 1d array
            the residual
        rms: int
            the rms value
    """

    res = np.array(model - data)
    rms = float(np.sqrt(np.nanmean(np.asarray(res, dtype=float) ** 2)))

    return res, rms


def peak_location_index(model: np.ndarray) -> int:
    """Return the index of the maximum value in a model array.
    Identifies the peak location by finding the position of the largest element.
    """
    return int(np.argmax(model))
