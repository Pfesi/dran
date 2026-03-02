# =========================================================================== #
# File: row_accessors.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Any, Iterable, Mapping, MutableMapping
import numpy as np
# =|========================================================================= #


def require_keys(row: Mapping[str, Any], keys: Iterable[str], 
                 context: str = "") -> None:
    """
    Ensure required keys exist in row.

    Raises:
        KeyError: If any key is missing.
    """
    missing = [k for k in keys if k not in row]
    if missing:
        prefix = f"{context}: " if context else ""
        raise KeyError(f"{prefix} Missing required keys: {missing}")


def get_float(
    row: Mapping[str, Any],
    key: str,
    default: float = float("nan"),
) -> float:
    """
    Read a float from a mapping. Returns default if the key is missing or 
    invalid.
    """
    try:
        value = row[key]
        if value is None:
            return default
        return float(value)
    except (KeyError, TypeError, ValueError):
        return default


def set_if_finite(row: MutableMapping[str, Any], 
                  key: str, value: float) -> None:
    """
    Set key to value only if value is finite.
    """
    if np.isfinite(value):
        row[key] = value
