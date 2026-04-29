# =========================================================================== #
# File: frequency_utils.py                                                    #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import sys
from pathlib import Path
from typing import Optional
from dran.utils.config import ObservationPathError
from dran.config.constants import (
    FREQUENCY_BANDS_MHZ, BAND_ALIASES, FREQ_ALIASES,
    _WAVELENGTH_BEAM_RE,_WAVELENGTH_ONLY_RE)
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
    # print('fr: ',frequency)
    
    try:
        frequency=int(FREQ_ALIASES[frequency])
    except:
        pass
    # print(FREQ_ALIASES[frequency]) 
    # sys.exit()
    # some files need a helper
    # if frequency==13:
    #     frequency=2270
    # if frequency==35:
    #     frequency=8280
    # if frequency==6:
    #     frequency=4800

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
        band: Band identifier such as 'L', 'S', 'C', 'CM', 'X', 'Ku', 'K', 'Ka'.
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


def _normalize_wavelength_key(value: float) -> str:
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text


def _resolve_band_to_frequency_mhz(band: str, source_freq_folder: str, p: Path) -> tuple[int, Optional[float], Optional[str]]:
    """
    Returns: (frequency_mhz, wavelength_cm, beam)
    """
    # Case A: wavelength + beam like 13NB, 3.5WB, etc.
    # print(band)
    m_beam = _WAVELENGTH_BEAM_RE.match(band)
    # print('beam: ',m_beam)
    if m_beam:
        wavelength_cm = float(m_beam.group("wavelength"))
        beam = m_beam.group("beam").upper()
        key = _normalize_wavelength_key(wavelength_cm)

        # print('>>> key: ',key)
        mhz_str = FREQ_ALIASES.get(key)
        if mhz_str is None:
            raise ObservationPathError(
                f"Unknown wavelength '{key} cm' in folder '{source_freq_folder}'. "
                f"Add it to FREQ_ALIASES: {p}"
            )
        return int(mhz_str), wavelength_cm, beam

    # Case B: wavelength only like 35, 13, 3.5
    m_wave = _WAVELENGTH_ONLY_RE.match(band)
    # print('m_wave: ',m_wave,m_wave.group("wavelength"))
    if m_wave:
        wavelength_cm = float(m_wave.group("wavelength"))
        key = _normalize_wavelength_key(wavelength_cm)

        mhz_str = FREQ_ALIASES.get(key)
        # print(mhz_str)
        if mhz_str is not None:
            return int(mhz_str), wavelength_cm, None

    # Case C: treat as frequency folder (must be digits)
    if band.isdigit():
        return int(band), None, None

    raise ObservationPathError(
        f"Unrecognized band token '{band}' in '{source_freq_folder}': {p}"
    )


def _read_frequency_from_fits_header(path: Path) -> tuple[str, str, str]:
    """
    Read observing frequency from the FITS header and convert it to the
    frequency, wavelength, and beam fields expected by DRAN.

    Returns:
        tuple[str, str, str]:
            frequency_mhz, wavelength_cm, beam
    """
    try:
        with fits.open(path) as hdul:
            header = hdul[2].header

            # Try the most likely header keys first.
            freq_mhz = (
                header.get("CENTFREQ")
                or header.get("FREQ")
                or header.get("RESTFREQ")
                # or header.get("CRVAL3")
            )

            if freq_mhz is None:
                raise ObservationPathError(
                    f"Could not determine frequency from FITS header: {path}"
                )

            # Convert to MHz if the value looks like Hz.
            freq_mhz = float(freq_mhz)

            wavelength_cm = header.get("CENTFREQ")[:-1]

            # You can refine beam logic if your project has exact rules.
            if freq_mhz<4000:
                beam = "SB"
            elif freq_mhz>=4000 and freq_mhz<=8000:
                beam="DB"
            else:
                beam="NB"

            return (
                freq_mhz,
                wavelength_cm,
                beam
            )

    except Exception as exc:
        raise ObservationPathError(
            f"Failed to read FITS header frequency from {path}: {exc}"
        ) from exc

