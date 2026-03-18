# =========================================================================== #
# File: computed_columns.py                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from itertools import chain
from typing import Any, List
from src.config.constants import (  # type: ignore
    COMM,
    COMM_WEATHER,
    JUP_WEATHER,
    LABEL_KWARGS_BY_BAND,
    WEATHER_BY_BAND,
)
from .labels import build_computed_column_labels
# =========================================================================== #


def build_computed_column_names(
    log: logging.Logger,
    band: str,
    src: str = "",
    seed: List[Any] | None = None,
) -> List[Any]:
    """
    Build the unified computed column list for a given band and optional source.

    Ordering:
    1. COMM
    2. COMM_WEATHER
    3. band-specific weather groups (from WEATHER_BY_BAND)
    4. computed labels (from build_computed_column_labels)

    Special case:
    - If band is K and src is JUPITER, append JUP_WEATHER to the band weather groups.

    Args:
        log: Logger.
        band: Band identifier (case-insensitive).
        src: Source name (case-insensitive).
        seed: Optional list to extend. If None, a new list is created.

    Returns:
        List[Any]: Assembled computed column list.
    """
    log.debug("Collecting computed column names.")

    norm_band = (band or "").strip().upper()
    src_upper = (src or "").strip().upper()

    if norm_band not in WEATHER_BY_BAND:
        raise ValueError(f"Unknown band: {norm_band}")

    computed: List[Any] = list(seed) if seed else []

    # Clone to avoid mutating the shared config.
    weather_groups = list(WEATHER_BY_BAND[norm_band])

    if norm_band == "K" and src_upper == "JUPITER":
        weather_groups.append(JUP_WEATHER)

    label_kwargs = LABEL_KWARGS_BY_BAND.get(norm_band, {})

    computed.extend(
        chain(
            COMM,
            COMM_WEATHER,
            *weather_groups,
            build_computed_column_labels(log, **label_kwargs),
        )
    )

    log.debug("Computed columns: %s", computed)
    return computed
