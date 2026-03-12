# =========================================================================== #
# File: frequency_utils.py                                                    #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from src.config.constants import FREQUENCY_BANDS_MHZ, BAND_ALIASES
# =========================================================================== #


def _normalize_band(band: str) -> str:
    """Normalize band identifiers to canonical uppercase (e.g., Ku -> KU)."""
    if band in BAND_ALIASES:
        return BAND_ALIASES[band]
    return band.strip().upper()


def get_band_from_frequency(frequency: float | int, log: logging.Logger) -> str:
    """
    Determine the satellite frequency band for a given frequency (in MHz).

    Args:
        frequency (float | int): Frequency in megahertz (MHz).

    Returns:
        str: The corresponding band identifier
             (e.g., 'L', 'S', 'C', 'CM', 'X', 'Ku', 'K', 'Ka').

    Raises:
        ValueError: If the input frequency is invalid or outside known bands.
    """

    log.debug('Getting frequency band from frequency in MHz')
    print(frequency)
    # some files need a helper
    if frequency==13:
        frequency=2270
    if frequency==35:
        frequency=8280
    if frequency==6:
        frequency=4800

    # Validate input type
    if not isinstance(frequency, (int, float)):
        raise TypeError(f"Frequency must be a numeric value, got {type(frequency).__name__}.")

    # Determine the corresponding frequency band
    for band_name, freq_range in FREQUENCY_BANDS_MHZ.items():
        if freq_range[0] <= frequency <= freq_range[1]:
            # Return canonical band keys (uppercase).
            return _normalize_band(band_name)

    # Frequency not in any known band
    valid_ranges = [
        f"{band}({band_info[0]}–{band_info[1]} MHz)"
        for band, band_info in FREQUENCY_BANDS_MHZ.items()
    ]

    raise ValueError(
        f"Frequency {frequency} MHz does not fall into any known band. "
        f"Valid ranges: {', '.join(valid_ranges)}."
    )


def get_frequency_range_from_band(band: str, log: logging.Logger) -> tuple[int, int]:
    """
    Return the frequency range in MHz for a given band identifier.

    Args:
        band: Band identifier such as L, S, C, X, Ku.
        log: Logger instance.

    Returns:
        Tuple of start and end frequency in MHz.

    Raises:
        TypeError: Invalid band type.
        ValueError: Unknown band.
    """
    log.debug("Getting frequency range from band")

    if not isinstance(band, str):
        raise TypeError(
            f"Band must be a string, got {type(band).__name__}."
        )

    # Accept legacy/user inputs but normalize to canonical keys.
    band_normalised = _normalize_band(band)

    if band_normalised not in FREQUENCY_BANDS_MHZ:
        valid_bands = ", ".join(FREQUENCY_BANDS_MHZ.keys())
        raise ValueError(
            f"Unknown band '{band}'. Valid bands: {valid_bands}."
        )

    return FREQUENCY_BANDS_MHZ[band_normalised]
