# =========================================================================== #
# File: schema.py                                                             #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Any, Dict
from .computed_columns import build_computed_column_names
from .observed_keys import build_observed_header_key_groups
# =========================================================================== #


LOW_BAND_COMPUTED_HDU_INDEX: int = 5
HIGH_BAND_COMPUTED_HDU_INDEX: int = 7


def build_header_key_schema(band: str, src: str, 
                            log: logging.Logger) -> Dict[str, Any]:
    """
    Build the complete header key schema (observed + computed) for band and source.

    Injection rule:
    - For L and S bands, computed columns are injected at HDU index 5.
    - For other bands, computed columns are injected at HDU index 7.

    Args:
        band: Band identifier.
        src: Source name (used for special-case computed columns).
        log: Logger.

    Returns:
        Dict[str, Any]: Observed groups plus computed group injected.
    """
    norm_band = (band or "").strip().upper()
    log.debug("Building complete header key schema for band=%s src=%s", 
              norm_band, src)

    header_groups: Dict[int, Any] = build_observed_header_key_groups(norm_band, 
                                                                     log)

    computed_columns = build_computed_column_names(
        log=log,
        band=norm_band,
        src=src,
        seed=[],
    )

    slot = LOW_BAND_COMPUTED_HDU_INDEX if norm_band in {"L", "S"} else HIGH_BAND_COMPUTED_HDU_INDEX
    header_groups[slot] = computed_columns

    # Preserve your previous return type shape (Dict[str, Any]).
    # If downstream expects Dict[int, ...], switch this annotation and return directly.
    return {str(k): v for k, v in header_groups.items()}
