# =========================================================================== #
# File: observed_keys.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Dict, List
from dran.config.constants import (
    C_KEYS,
    FS_KEYS,
    ND_KEYS,
    PR_KEYS,
)
# =========================================================================== #


def build_observed_header_key_groups(band: str, 
                                log: logging.Logger) -> Dict[int, List[str]]:
    """
    Build observed header key groups for a given band.

    The indices reflect the existing downstream expectations in your pipeline.

    For L/S:
        0: PR_KEYS
        1: FS_KEYS
        2: ND_KEYS
        3: []
        4: C_KEYS
        5: []  (reserved for computed injection)

    For other bands:
        0: PR_KEYS
        1: FS_KEYS
        2: ND_KEYS
        3: []
        4: []
        5: []
        6: C_KEYS
        7: []

    Args:
        band: Band identifier (case-insensitive).
        log: Logger.

    Returns:
        Dict[int, List[str]] mapping group index to cloned key lists.
    """
    norm_band = (band or "").strip().upper()
    log.debug("Building observed header key groups for band=%s", norm_band)

    if norm_band in {"L", "S"}:
        groups: Dict[int, List[str]] = {
            0: list(PR_KEYS),
            1: list(FS_KEYS),
            2: list(ND_KEYS),
            3: [],
            4: list(C_KEYS),
            5: [],
        }
    else:
        groups = {
            0: list(PR_KEYS),
            1: list(FS_KEYS),
            2: list(ND_KEYS),
            3: [],
            4: [],
            5: [],
            6: list(C_KEYS),
            7: [],
        }

    log.debug("Observed groups: %s", groups)
    return groups
