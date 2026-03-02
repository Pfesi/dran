from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional


WAVELENGTH_CM_TO_MHZ: dict[str, str] = {
    "13": "2280",
    "3.5": "8280",
    "35": "8280",
    "18": "1720",
    "2.5": "12218",
    "6": "4800",
    "1.3": "22040",
}

_WAVELENGTH_BEAM_RE = re.compile(
    r"^(?P<wavelength>\d+(?:\.\d+)?)(?:cm)?(?P<beam>[A-Za-z]+)$",
    flags=re.IGNORECASE,
)

_WAVELENGTH_ONLY_RE = re.compile(
    r"^(?P<wavelength>\d+(?:\.\d+)?)(?:cm)?$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ObservationPathParts:
    root_data_dir: Path
    category: str
    source: str
    frequency: int
    filename: str
    full_path: Path

    # Optional metadata. Leave if you do not need it.
    wavelength_cm: Optional[float] = None
    beam: Optional[str] = None
    band_folder: Optional[str] = None


class ObservationPathError(ValueError):
    pass


def _normalize_wavelength_key(value: float) -> str:
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text


def _resolve_band_to_frequency_mhz(band: str, source_freq_folder: str, p: Path) -> tuple[int, Optional[float], Optional[str]]:
    """
    Returns: (frequency_mhz, wavelength_cm, beam)
    """
    # Case A: wavelength + beam like 13NB, 3.5WB, etc.
    m_beam = _WAVELENGTH_BEAM_RE.match(band)
    if m_beam:
        wavelength_cm = float(m_beam.group("wavelength"))
        beam = m_beam.group("beam").upper()
        key = _normalize_wavelength_key(wavelength_cm)

        mhz_str = WAVELENGTH_CM_TO_MHZ.get(key)
        if mhz_str is None:
            raise ObservationPathError(
                f"Unknown wavelength '{key} cm' in folder '{source_freq_folder}'. "
                f"Add it to WAVELENGTH_CM_TO_MHZ: {p}"
            )
        return int(mhz_str), wavelength_cm, beam

    # Case B: wavelength only like 35, 13, 3.5
    m_wave = _WAVELENGTH_ONLY_RE.match(band)
    if m_wave:
        wavelength_cm = float(m_wave.group("wavelength"))
        key = _normalize_wavelength_key(wavelength_cm)

        mhz_str = WAVELENGTH_CM_TO_MHZ.get(key)
        if mhz_str is not None:
            return int(mhz_str), wavelength_cm, None

    # Case C: treat as frequency folder (must be digits)
    if band.isdigit():
        return int(band), None, None

    raise ObservationPathError(
        f"Unrecognized band token '{band}' in '{source_freq_folder}': {p}"
    )


def parse_observation_path(path_str: str) -> ObservationPathParts:
    """
    Parse observation file paths for DRAN.

    Supported layouts:
    data/calibration/3C123/12178/file.fits
    data/calibration/3C123_12178/file.fits
    data/calibration/3C123_13NB/file.fits
    data/calibration/3C123_13NB_dichroic_on/file.fits
    data/calibration/3C123_35/file.fits
    data/calibration/3C123_3.5NB/file.fits
    """
    p = Path(path_str).expanduser().resolve()
    parts = p.parts

    if "data" not in parts:
        raise ObservationPathError(f"Missing 'data' directory in path: {p}")

    data_idx = parts.index("data")
    rel = parts[data_idx + 1 :]

    if len(rel) < 3:
        raise ObservationPathError(f"Invalid observation path structure: {p}")

    category = rel[0]
    filename = rel[-1]

    # Layout A: data/category/source/frequency/file
    if len(rel) >= 4:
        source = rel[1]
        band = rel[2]

        freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
            band=band,
            source_freq_folder=f"{source}_{band}",
            p=p,
        )

        return ObservationPathParts(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=freq_mhz,
            filename=filename,
            full_path=p,
            wavelength_cm=wavelength_cm,
            beam=beam,
            band_folder=band,
        )

    # Layout B/C: data/category/source_band[_extra_tokens]/file
    source_freq_folder = rel[1]
    if "_" not in source_freq_folder:
        raise ObservationPathError(f"Missing source_<band> pattern: {p}")

    sf_tokens = [t for t in source_freq_folder.split("_") if t]
    if len(sf_tokens) < 2:
        raise ObservationPathError(f"Missing band token in folder '{source_freq_folder}': {p}")

    source = sf_tokens[0]
    candidate_tokens = sf_tokens[1:]

    band_token: Optional[str] = None
    for token in candidate_tokens:
        # Accept first token that looks like either:
        #  - digits (frequency or wavelength-only)
        #  - wavelength+beam (13NB, 3.5WB, etc.)
        #  - decimal wavelength-only (3.5)
        if token.isdigit():
            band_token = token
            break
        if _WAVELENGTH_BEAM_RE.match(token):
            band_token = token
            break
        if _WAVELENGTH_ONLY_RE.match(token):
            band_token = token
            break

    if band_token is None:
        raise ObservationPathError(
            f"Unrecognized band folder in '{source_freq_folder}': {p}"
        )

    freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
        band=band_token,
        source_freq_folder=source_freq_folder,
        p=p,
    )

    return ObservationPathParts(
        root_data_dir=Path(*parts[: data_idx + 1]),
        category=category,
        source=source,
        frequency=freq_mhz,
        filename=filename,
        full_path=p,
        wavelength_cm=wavelength_cm,
        beam=beam,
        band_folder=band_token,
    )