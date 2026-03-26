# =========================================================================== #
# File: labels.py                                                             #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from itertools import product
from typing import List, Tuple

# =========================================================================== #


def build_computed_column_labels(
    log: logging.Logger,
    pol: Tuple[str, ...] = ("L", "R"),
    pos: Tuple[str, ...] = ("O",),
    beam: Tuple[str, ...] = ("",),
    cols: Tuple[str, ...] = ("RMS", "BSLOPE", "BRMS", "FLAG", "S2N", "TA", "TAPEAKLOC"),
) -> List[str]:
    """
    Generate computed column labels.

    Rules:
    - Labels are built from beam + position + polarization + base column name.
    - For TA, append TAERR.
    - If position codes include multiple entries and include "O", append:
      - PC
      - corrected TA (prefixed with C)
      - corrected TAERR

    Args:
        log: Logger for diagnostics.
        pol: Polarizations, for example ("L", "R").
        pos: Position codes, for example ("N", "S", "O").
        beam: Beam identifiers, for example ("A", "B", "").
        cols: Base column names.

    Returns:
        Flattened list of label strings.
    """
    log.debug("Building computed column labels.")
    include_pc = len(pos) > 1

    labels: List[str] = []
    beam_independent = {"RMS", "BRMS","BSLOPE", "FLAG"}

    for p, s, col in product(pol, pos, cols):
        if col in beam_independent:
            base = f"{s}{p}{col}"
            labels.append(base)
            continue

        for b in beam:
            base = f"{b}{s}{p}{col}"
            if col == "TA":
                labels.append(base)
                labels.append(f"{base}ERR")

                if include_pc and s == "O":
                    labels.append(f"{b}{s}{p}PC")
                    labels.append(f"{b}C{s}{p}{col}")
                    labels.append(f"{b}C{s}{p}{col}ERR")
            else:
                labels.append(base)

    log.debug("Computed labels: %s", labels)
    return labels
