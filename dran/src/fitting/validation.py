# =========================================================================== #
# File: validation.py                                                         #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import numpy as np
# =========================================================================== #


def validate_xy(x: np.ndarray, y: np.ndarray, log: logging.Logger) -> int:
    """
    Returns:
        flag int. 0 means pass.
    Raises:
        ValueError on invalid inputs.
    """
    log.debug("Validating x, y inputs")

    x = np.asarray(x)
    y = np.asarray(y)

    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("x and y must be 1D arrays.")

    if x.size != y.size:
        raise ValueError("x and y must have the same length.")

    if x.size < 5:
        raise ValueError("Not enough samples to fit beam. Need >= 5.")

    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("Found non-finite values in x or y.")

    log.debug("Input validation passed")
    return 0
