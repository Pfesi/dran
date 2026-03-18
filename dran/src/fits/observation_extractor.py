# =========================================================================== #
# File: observation_extractor.py                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
from src.fits.hdu_rules import scan_hdu_indices
from src.fits.lazy_reader import LazyFITSReader
from src.fits.types import ObsRecord
from src.config.paths import ProjectPaths
from src.utils.frequency_utils import get_band_from_frequency
from src.obs.records import build_observation_record
from src.header import build_header_key_schema
from src.obs.populate import  populate_scan_arrays
from src.calibration.atmosphere.meteo_water_vapour import (
    add_water_vapour_fields)
from src.calibration.atmosphere.atmos_frontend_dispatch import (
    dispatch_atmospheric_correction)
from src.calibration.errors import UnsupportedFrontendError
from src.utils.fs import create_dir
from src.utils.invalid_path_registry import  record_invalid_path_once
# =========================================================================== #


def extract_observation(path: Path, 
                        paths: ProjectPaths,
                        band: str,
                        log: logging.Logger) -> ObsRecord:
    """
    Extract one observation record from a FITS file path.

    This preserves your existing behavior:
    - Uses headers to determine SRCNAME, CENTFREQ, BAND, HDULEN.
    - Populates a dict record using init_obs_row and get_complete_header_set.
    - Extracts scan arrays and derives weather quantities.

    Returns
    -------
    ObsRecord
        A populated observation record dict.
    """

    with LazyFITSReader(path, memmap=True, cache_data=True) as reader:

        hdu_len = reader.hdu_count()
        obs = _extract_headers(reader=reader, paths=paths,
                               hdu_len=hdu_len, band=band,
                               log=log)
        
        # Prefer the header-derived band for validation and logging.
        derived_band = (obs.get("BAND") or band).strip().upper()

        if hdu_len<=5 and derived_band in {'L','S'}:
            pass
        elif hdu_len > 5 and derived_band in {'C','CM','X','KU','K','KA'}:
            pass
        else:
            msg=(
                "Invalid obs file: "
                f"HDU_LEN={hdu_len}, band(path)={band}, band(header)={derived_band}"
            )
            log.warning(msg)
            log.info('Stopped processing')
            record_invalid_path_once(path, paths, log, msg)
            obs["SCAN_ERROR"] = msg
            
            if derived_band in {'L','S'}:
                for pol in {"L","R"}:
                    obs[f'ZC_{pol}CPDATA'] = np.array([])
            else:
                for pos in {"N","S","O"}:
                    for pol in {"L","R"}:
                        if pos=="O":
                            obs[f'ZC_{pol}CPDATA'] =np.array([])
                        else:
                            obs[f'HP{pos}Z_{pol}CPDATA'] =np.array([])
                
            obs['OFFSET']=np.array([])
            return obs
        
        _extract_scans(reader=reader, obs=obs, log=log)
        if obs.get("SCAN_ERROR") is None:
            _apply_weather(obs=obs, log=log)

        return obs


def _extract_headers(reader: LazyFITSReader,
                     paths: ProjectPaths,
                     hdu_len: int, 
                     band: str,
                     log: logging.Logger) -> ObsRecord:
    """Extract core FITS headers and initialize an observation record.
    Reads required headers, derives band from CENTFREQ, builds and logs the 
    observation metadata, prepares output directories, and populates 
    additional header fields across expected HDUs.
    """

    if hdu_len < 3:
        obs = build_observation_record(
            reader.path, paths, "UNKNOWN", 0.0, band, hdu_len, log
        )
        obs["SCAN_ERROR"] = (
            f"Invalid FITS file: expected HDU 0 and 2, got {hdu_len} HDUs"
        )
        return obs

    hdr0 = reader.get_header(0)
    hdr2 = reader.get_header(2)

    srcname = str(hdr0.get("OBJECT"))
    centfreq = hdr2.get("CENTFREQ")


    if centfreq is None:
        centfreq = hdr2.get("CENTFRQ1")
        if centfreq is None:
            raise KeyError("CENTFREQ missing in HDU 2 header")

    
    band = get_band_from_frequency(centfreq, log)

    obs: ObsRecord = build_observation_record(
        reader.path, paths, srcname, centfreq, band, hdu_len, log)
    
    log.debug(f"Initialized observation record: {obs}")
    log.info("*" * 80)
    log.info("Source parameters")
    log.info("*" * 80)
    log.info(f"Target: {srcname}")
    log.info(f"Frequency: {centfreq} MHz")
    log.info(f"Band: {band}")
    log.info(f"File name: {obs.get('FILENAME')}")
    log.info(f"Save processed plots to: {obs.get('PLOT_SAVE_DIR')}")
    log.info("*" * 80)
    
    obs['CENTFREQ'] = centfreq
    
    header_keys = build_header_key_schema(band, srcname, log)
    log.debug(f"Header key map loaded. HDUs expected: {len(header_keys)}")

    create_dir(obs['PLOT_SAVE_DIR'],log)
    _populate_header_fields(
        reader=reader,
        obs=obs,
        header_keys=header_keys,
        hdu_len=hdu_len,
        log=log,
        band=band
    )

    return obs


def _populate_header_fields(
    reader: LazyFITSReader,
    obs: ObsRecord,
    header_keys: Dict[int, List[str]],
    hdu_len: int,
    log: logging.Logger,
    band:str
) -> None:
    """
    Populate obs with header fields.

    This retains your existing pattern where header_keys is indexed by HDU 
    index, plus an extra final entry for derived or optional fields.
    """

    
    for row, keys_for_hdu in header_keys.items():
        row=int(row)

        if row < hdu_len:
            header = reader.get_header(row)
            if band=='X' or band=="C":
                if row==2:
                    # use low noise diode
                    log.debug('Using low noise diode data')
                    hzperk=['HZPERK1','HZKERR1','HZPERK2','HZKERR2']
                    keys_for_hdu+=hzperk
            else:
                # print(row,hdu_len-1)
                if row==hdu_len-1:
                    log.debug('Using high noise diode data')
                    hzperk=['HZPERK1','HZKERR1','HZPERK2','HZKERR2']
                    keys_for_hdu+=hzperk
                else:
                    pass

            for key in keys_for_hdu:
                if key in header:
                    val = header.get(key)
                    
                    # Do not clobber existing valid values with None.
                    if val is None and obs.get(key) is not None:
                        continue
                    obs[key] = val
                    if key=='DATE':
                        date_val = header.get(key)
                        if isinstance(date_val, str) and "T" in date_val:
                            date = date_val.split("T", 1)
                            obs["OBSDATE"] = date[0]
                            obs["OBSTIME"] = date[1]
                        else:
                            obs["OBSDATE"] = None
                            obs["OBSTIME"] = None
                else:
                    if key not in obs or obs.get(key) is None:
                        obs[key] = None
        else:
            for key in keys_for_hdu:
                if key in {"HUMIDITY", "TAMBIENT"}:
                    continue
                if key not in obs or obs.get(key) is None:
                    obs[key] = None

    log.debug("Header fields populated into observation record.")


def _extract_scans(reader: LazyFITSReader, 
                   obs: ObsRecord, log: logging.Logger) -> None:
    
    """Extract scan data from configured FITS HDUs into the observation record.
    Validates HDU length metadata, resolves the scan HDU indices, and 
    iterates through each scan HDU to load and store scan arrays.
    """
    
    
    log.info('Fetching observation scans')
    hdus = reader.list_hdus()
    hdu_len = obs.get("HDULEN")

    if not isinstance(hdu_len, int):
        raise KeyError("HDULEN missing from observation record")

    indices = scan_hdu_indices(hdu_len)
    if not indices:
        log.warning(f"No scan HDU indices configured for HDULEN={hdu_len}")
        return

    for i in indices:
        if obs.get("SCAN_ERROR") is not None:
            # Stop further scan extraction if a fatal scan error is recorded.
            return
        _extract_single_scan(reader=reader, obs=obs, hdus=hdus, index=i, log=log)


def _extract_single_scan(
    reader: LazyFITSReader,
    obs: ObsRecord,
    hdus: List[Dict[str, Any]],
    index: int,
    log: logging.Logger,
) -> None:
    """Extract a single scan HDU and populate observation scan arrays.
    Validates the HDU index, derives a header name (including legacy Drift 
    mapping), reads the scan table, logs available columns, and delegates 
    storage and derived-field computation to populate_scan_arrays.
    """
   
    if index < 0 or index >= len(hdus):
        log.warning(f"Scan HDU index out of range: {index}")
        return

    hdu_name = str(hdus[index].get("extname", ""))
    header_name = hdu_name.split("_")[-1] if hdu_name else str(index)

    # support for older file systems from 2004
    if header_name=='Drift':
        if index==3:
            header_name='HPNZ'
        elif index==4:
            header_name='ZC'
        elif index==5:
            header_name='HPSZ'
        else:
            # Unexpected HDU layout: flag and stop processing this file.
            log.error("Invalid drift-scan HDU index: %s", index)
            obs["SCAN_ERROR"] = f"Invalid drift-scan HDU index: {index}"
            return
    if header_name=="HPNA":
        header_name="HPNZ"
    if header_name=="ONA":
        header_name="ZC"
    if header_name=="HPSA":
        header_name="HPSZ"

    log.info(f"Extracting scan data from HDU {index} ({header_name})")
    
    scans = reader.get_data(index)
    names = None
    try:
        names = getattr(scans, "names", None)
        if names is None and hasattr(scans, "dtype"):
            names = scans.dtype.names
        log.debug(f"HDU {index} table columns: {names}")
    except Exception:
        log.debug(f"HDU {index} table columns: unknown")

    populate_scan_arrays(obs, scans, index, header_name, names,log)


def _apply_weather(obs: ObsRecord, log: logging.Logger) -> None:
    """Apply weather and atmospheric corrections to an observation record.
    Adds water vapour related fields and runs the configured atmospheric 
    correction routine.
    """

    add_water_vapour_fields(obs, log)
    extname = str(obs.get("EXTNAME", "") or "").strip()
    if not extname:
        log.warning("Missing EXTNAME; skipping atmospheric calibration")
        return
    try:
        dispatch_atmospheric_correction(obs, log)
    except UnsupportedFrontendError as exc:
        log.warning("Atmospheric calibration skipped: %s", exc)
