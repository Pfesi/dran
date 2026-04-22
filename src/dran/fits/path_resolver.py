# =========================================================================== #
# File: path_resolver.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional
import sys
import numpy as np
from astropy.io import fits
from dran.config.constants import FREQ_ALIASES
from dran.utils.frequency_utils import get_band_from_frequency
# =========================================================================== #


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


@dataclass(frozen=True)
class ObservationPathPartsFolder:
    root_data_dir: Path
    category: str
    source: str
    frequency: int
    foldername: str
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


class ObservationPathError(Exception):
    """Raised when an observation path cannot be parsed."""

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
    data/calibration/Jup/file.fits
    """
    p = Path(path_str).expanduser().resolve()
    parts = p.parts

    if "data" not in parts:
        raise ObservationPathError(f"Missing 'data' directory in path: {p}")

    data_idx = parts.index("data")
    rel = parts[data_idx + 1 :]

    # if len(rel) < 3:
    #     raise ObservationPathError(f"Invalid observation path structure: {p}")

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
        
        if rel[0]=='12GHz_continuum':
                freq="12218"
                wav='2.5'
                bm="NB"
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=rel[1],
                    frequency=freq,
                    filename=rel[-1],
                    full_path=p,
                    wavelength_cm=wav,
                    beam=bm,
                    band_folder="2.5",
                )
                
        elif rel[0]=='22GHz_continuum':
                freq="22040"
                wav='1.3'
                bm="NB"
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=rel[1],
                    frequency=freq,
                    filename=rel[-1],
                    full_path=p,
                    wavelength_cm=wav,
                    beam=bm,
                    band_folder="1.3",
                )
                              
        else:
            try:
                source = rel[1]
                freq_mhz, wavelength_cm, beam = _read_frequency_from_fits_header(p)
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=source,
                    frequency=freq_mhz,
                    filename=filename,
                    full_path=p,
                    wavelength_cm=wavelength_cm,
                    beam=beam,
                    band_folder="header_inferred",
                )
            except:
                print('***',source_freq_folder)
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
        # raise ObservationPathError(
        #     f"Unrecognized band folder in '{source_freq_folder}': {p}"
        # )
        return ObservationPathParts(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=np.nan,
            filename=filename,
            full_path=p,
            wavelength_cm=None,
            beam="",
            band_folder=None,
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
    
def parse_observation_path_if_folder(path_str: str) -> ObservationPathPartsFolder:
    """
    Parse observation file paths for DRAN.

    Supported layouts:
    data/calibration/3C123/12178/
    data/calibration/3C123_12178/
    data/calibration/3C123_13NB/
    data/calibration/3C123_13NB_dichroic_on/
    data/calibration/3C123_35/
    data/calibration/3C123_3.5NB/
    data/calibration/3C123/
    data/calibration/Jup/
    """
    
    print(path_str,'\n')
    
    p = Path(path_str).expanduser().resolve()
    parts = p.parts
    # print(parts)
    if "data" not in parts:
        raise ObservationPathError(f"Missing 'data' directory in path: {p}")

    data_idx = parts.index("data")
    rel = parts[data_idx + 1 :]
    print(rel,'\n')
    # if len(rel) < 2:
    #     raise ObservationPathError(f"Invalid observation path structure: {p}")

    category = rel[0]
    foldername = rel[-1]

    if rel[0]==rel[-1]:
        # print('out',Path(*parts[: data_idx + 1]),category,source,freq_mhz,foldername,p,wavelength_cm,beam,band_token)
        return ObservationPathPartsFolder(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=None,
            frequency=None,
            foldername=foldername,
            full_path=p,
            wavelength_cm=None,
            beam=None,
            band_folder=None,
        )
    
    # Layout A: data/category/source/frequency/
    # print(category,foldername,rel,'\n')
    if len(rel) >= 3:
        source = rel[1]
        band = rel[2]

        freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
            band=band,
            source_freq_folder=f"{source}_{band}",
            p=p,
        )

        return ObservationPathPartsFolder(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=freq_mhz,
            foldername=foldername,
            full_path=p,
            wavelength_cm=wavelength_cm,
            beam=beam,
            band_folder=band,
        )

    # Layout B/C: data/category/source_band[_extra_tokens]/
    source_freq_folder = rel[1]
    print(source_freq_folder)
    if "_" not in source_freq_folder:
        
            
        raise ObservationPathError(f"Missing source_<band> pattern: {p}")

    sf_tokens = [t for t in source_freq_folder.split("_") if t]
    # print(sf_tokens)
    if len(sf_tokens) < 2:
        raise ObservationPathError(f"Missing band token in folder '{source_freq_folder}': {p}")

    source = sf_tokens[0]
    candidate_tokens = sf_tokens[1:]
    # print(candidate_tokens)
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
    # print(band_token)
    if band_token is None:
        raise ObservationPathError(
            f"Unrecognized band folder in '{source_freq_folder}': {p}"
        )

    freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
        band=band_token,
        source_freq_folder=source_freq_folder,
        p=p,
    )
    # print('out',Path(*parts[: data_idx + 1]),category,source,freq_mhz,foldername,p,wavelength_cm,beam,band_token)
    return ObservationPathPartsFolder(
        root_data_dir=Path(*parts[: data_idx + 1]),
        category=category,
        source=source,
        frequency=freq_mhz,
        foldername=foldername,
        full_path=p,
        wavelength_cm=wavelength_cm,
        beam=beam,
        band_folder=band_token,
    )