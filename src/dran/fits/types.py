# =========================================================================== #
# File: types.py                                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Any, Dict, List, Optional, TypedDict,Mapping, Sequence
from dataclasses import dataclass
import numpy as np
# =========================================================================== #


class HduSummary(TypedDict):
    index: int
    extname: str
    type: str
    rows: int | str
    cols: int | str
    shape: int | str
    has_data: bool


class ObsRecord(TypedDict, total=False):
    """
    Observation record produced by extraction.

    This matches the existing behavior where keys are added dynamically.
    It stays flexible, while still providing a named type for clarity.
    """

    FILEPATH: str
    FILENAME: str
    OBSNAME: str
    PLOT_SAVE_DIR: str
    HDULEN: int
    OBJECT: str
    CENTFREQ: float
    BAND: str
    SCAN_ERROR: Optional[str]

    # Scan arrays and derived quantities are added by populate_scan_arrays
    # and weather calculations, so they remain untyped here on purpose.
    _raw: Dict[str, Any]


@dataclass(frozen=True, slots=True)
class ScanArrays:
    """
    Normalized, analysis-ready arrays for one scan.

    Notes
    - x is the independent axis. For example frequency, offset, or sample index.
    - y is the primary dependent series. For example TA or power.
    - meta keeps scalar values that you want to show in UI or logs.
    - series lets you store multiple named arrays if you have more than one y.
    """

    x: np.ndarray
    y: np.ndarray

    scan_id: str
    band: str
    source: str

    meta: Mapping[str, Any]
    series: Mapping[str, np.ndarray]


@dataclass(frozen=True, slots=True)
class PopulateOptions:
    """
    Options to control how arrays are constructed from FITS content.
    """

    x_column: str
    y_column: str

    scan_id_column: str = "SCAN"
    source_column: str = "SRC"
    band_column: str = "BAND"

    drop_non_finite: bool = True
    sort_by_x: bool = True

    extra_series: Optional[Sequence[str]] = None


ObsRecords = List[Dict[str, Any]]
