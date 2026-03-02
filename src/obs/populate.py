# =========================================================================== #
# File: populate.py                                                           #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Any, List, MutableMapping
import numpy as np
from src.obs.conversion import counts_to_kelvin
# =========================================================================== #


def _as_1d(value: Any) -> np.ndarray:
    """Convert input to a one-dimensional NumPy array.
    Flattens multi-dimensional inputs and wraps scalar values into a 
    single-element array.
    """
    
    arr = np.asarray(value)
    if arr.ndim > 1:
        return arr.ravel()
    if arr.ndim == 0:
        return arr.reshape(1)
    return arr

def _get_col(table: Any, name: str, log: logging.Logger) -> np.ndarray:
    """Retrieve a column from a table as a one-dimensional NumPy array.
    Logs the column access and raises a clear KeyError if the column is 
    missing or inaccessible.
    """
    
    log.debug(f"getting column: {name}") # from {table}")
    try:
        return _as_1d(table[name])
    except Exception as exc:
        log.error(f"Missing column: {name}, -> {exc}")
        return np.array([0])

def _is_invalid_scalar(value: Any) -> bool:
    if value is None:
        return True
    try:
        arr = np.asarray(value)
    except Exception:
        return False
    if arr.shape == ():
        try:
            return not np.isfinite(float(arr))
        except Exception:
            return False
    return False

def _store_on_obs(obs: Any, key: str, value: Any) -> None:
    """Store a value on an observation object.
    Sets the value using an uppercase key for mappings, or as an attribute 
    for object-based observations.
    """
    if isinstance(obs, MutableMapping):
        obs[key.upper()] = value
        return
    setattr(obs, key, value)

def populate_scan_arrays(
    obs: Any,
    scans_table: Any,
    hdu_index: int,
    header_name: str,
    column_names: List,
    log: logging.Logger
) -> None:
    """Populate observation fields from a scans table.
    Extracts metadata and scan data for the given HDU, computes derived 
    quantities for ZC headers, converts LCP and RCP counts to Kelvin, and 
    stores results on the observation object.
    """

    # print('&&&& ',hdu_index,header_name)
    if scans_table is None:
        log.warning(f"No scans table in HDU {hdu_index} ({header_name})")
        return

    if not column_names:
        log.warning("No column names found for HDU %s (%s).", hdu_index, header_name)
        column_names = []
    # print(scans_table)
    if 'ZC' in header_name:
        n = None
        for col in column_names:
            if 'Count' in col:
                pass
            else:
                # print(col)
                data = _get_col(scans_table, col, log)
                n = len(data)
                mid = n // 2
                value = data[mid]
                # Avoid clobbering valid header values with None/NaN from scan tables.
                if _is_invalid_scalar(value) and col in obs and obs[col] is not None:
                    continue
                _store_on_obs(obs, col, value)
                log.debug(f"Added {col}  = {value}, from HDU {hdu_index} ({header_name}).")
        
        centfreq = obs.get("CENTFREQ")
        try:
            centfreq_val = float(np.asarray(centfreq).item())
        except Exception:
            log.warning("CENTFREQ missing/invalid; skipping LOGFREQ")
        else:
            obs["LOGFREQ"] = float(np.log10(centfreq_val))
        obs['ZA']=90.0 - obs['ELEVATION']

        # Offset array requires SCANDIST; guard if missing
        if n is None:
            try:
                n = len(_get_col(scans_table, "Count1", log))
            except Exception:
                n = 0

        try:
            scan_dist = _get_col(obs, "SCANDIST", log)
        except Exception:
            scan_dist = float(n)

        try:
            scan_dist = float(np.asarray(scan_dist).item())  # works for scalar/0-d arrays
        except Exception:
            scan_dist = float(n)  # fallback: use number of samples

        offset = np.linspace(-scan_dist / 2.0, scan_dist / 2.0, n)
        _store_on_obs(obs,'OFFSET',offset)

    else:
        # print('--- ',header_name)
        pass

    # get obs
    lcp_counts = _get_col(scans_table,"Count1",log)
    rcp_counts = _get_col(scans_table,"Count2",log)

    lcp = counts_to_kelvin(lcp_counts, _get_col(obs, "HZPERK1",log))
    rcp = counts_to_kelvin(rcp_counts, _get_col(obs, "HZPERK2",log))

    _store_on_obs(obs, f"{header_name}_lcpdata",lcp)
    _store_on_obs(obs, f"{header_name}_rcpdata",rcp)
