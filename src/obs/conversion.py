# =========================================================================== #
# File: conversion.py                                                         #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Any
import numpy as np
# =========================================================================== #


def counts_to_kelvin(counts: np.ndarray, hz_per_k: Any) -> np.ndarray:
    """
    Convert raw detector counts to Kelvin using a Hz-per-K scale factor.

    The conversion used mirrors the original behavior:
    (counts - counts[0]) / scale

    If conversion fails for any reason (missing scale, invalid scale, scale=0),
    the function returns a zero array of the same length.

    Parameters
    ----------
    counts:
        Input counts array.
    hz_per_k:
        Scale factor (Hz per Kelvin). Accepts any value convertible to float.

    Returns
    -------
    np.ndarray
        Converted array in Kelvin, or a safe zero fallback.
    """
    counts = np.asarray(counts)

    # Safe fallback for empty input.
    if counts.size == 0:
        return np.asarray([], dtype=float)

    try:
        scale = float(hz_per_k)
        if scale == 0.0:
            raise ZeroDivisionError("hz_per_k scale is zero.")
        return (counts.astype(float) - float(counts[0])) / scale
    except Exception:
        return np.zeros(counts.size, dtype=float)
