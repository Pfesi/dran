# =========================================================================== #
# File: spline_models.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Optional
import numpy as np
from scipy import interpolate
# =========================================================================== #


def spline_fit_1d(
    y: np.ndarray,
    anchor_points: int = 9,
    order: int = 3,
    log: Optional[logging.Logger] = None,
) -> np.ndarray:
    """
    Spline smoothing over y values using index space.
    """
    
    y_arr = np.asarray(y, dtype=float).ravel()
    n = y_arr.size

    if y_arr.ndim != 1:
        raise ValueError(f"y must be 1-D. Got shape {y_arr.shape}.")

    if anchor_points < 1:
        return y_arr

    if order < 1 or order > 5:
        raise ValueError("order must be in [1, 5].")

    if n <= anchor_points * 2:
        return y_arr

    if log is not None:
        log.debug("Spline fit: anchor_points=%d order=%d", anchor_points, order)

    x_idx = np.linspace(1.0, float(n), n)

    interior_count = anchor_points - 1
    if interior_count > 0:
        knot_pos = np.linspace(1.0, float(n), interior_count + 2)[1:-1]
        knot_pos = np.unique(knot_pos.astype(int))
    else:
        knot_pos = np.array([], dtype=int)

    try:
        tck = interpolate.splrep(x_idx, y_arr, k=order, task=-1, t=knot_pos)
        fit = interpolate.splev(x_idx, tck, der=0)
        return np.asarray(fit, dtype=float)
    except Exception:
        return y_arr
