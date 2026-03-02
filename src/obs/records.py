# =========================================================================== #
# File: records.py                                                            #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from pathlib import Path
from typing import Any, Dict
from src.config.paths import ProjectPaths
# =========================================================================== #


def build_observation_record(
    path: Path,
    paths:ProjectPaths,
    source_name: str,
    frequency_mhz: float,
    band: str,
    hdu_len: int,
    logger: logging.Logger,
) -> Dict[str, Any]:
    """
    Build an observation result record with common file metadata fields.

    Notes
    - Keys are uppercase to match a "record schema" style used by CSV/DB 
    exports.
    - "band" is accepted for schema completeness, even if not used yet.

    Parameters
    ----------
    path:
        Input FITS file path.
    source_name:
        Source name. Stored in normalized form for folder conventions.
    frequency_mhz:
        Center frequency derived from directory or context. Rounded to int for 
        folder naming.
    band:
        Band label (e.g., L/S/C/X). Stored for completeness.
    hdu_len:
        Number of HDUs in the FITS file.
    logger:
        Application logger.

    """
    
    logger.debug("Building observation record with common file metadata fields.")

    normalized_source = source_name.replace(" ", "").upper()
    freq_int = int(frequency_mhz)

    return {
        "FILEPATH": str(path),
        "FILENAME": path.name,
        "OBSNAME":path.name[:18],
        "DIR_FREQ": freq_int,  # convention: frequency folder name (MHz)
        "DIR_NAME": normalized_source,  # convention: source folder name
        "BAND": band,
        "HDULEN": hdu_len,
        "PLOT_SAVE_DIR": f"{str(paths.plots_dir)}/{normalized_source}/{freq_int}/",
        # Populated when scan extraction fails; stored in DB for diagnostics.
        "SCAN_ERROR": None,
    }
