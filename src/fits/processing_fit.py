# =========================================================================== #
# File: processing_fit.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Any, Dict, List, Mapping, Sequence
import os
import numpy as np
import argparse
import logging
import json
from dataclasses import asdict, is_dataclass
import math 
import sys
from src.config.constants import DIAGNOSTICS_DIRNAME
from src.utils.fs import clear_diagnostics_dir
from src.config.paths import ProjectPaths
from src.fitting.pipeline import fit_scan, fit_scan_db
from src.fitting.models import sig_to_noise
from src.calibration.calibrate import calibrate_pointing_corrected_ta
# =========================================================================== #


def to_jsonable(value: Any) -> Any:
    """Convert a value into a JSON-serializable form.
    Handles dataclasses, objects with to_dict, scalars, collections, 
    mappings, and plain objects, replacing non-finite floats with null 
    equivalents.
    """
    
    if value is None:
        return None

    if is_dataclass(value):
        return asdict(value)

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]

    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}

    # Plain Python objects, like ScanQualityResult
    try:
        return {k: to_jsonable(v) for k, v in vars(value).items()}
    except TypeError:
        return str(value)
    

def dumps_json(value: Any) -> str:
    """JSON-dump with a safe default conversion."""
    return json.dumps(to_jsonable(value), ensure_ascii=False)


def _fit_one_scan(
    row: Mapping[str, Any],
    y: Any,
    band: str,
    out_path: str,
    paths:ProjectPaths,
    log: logging.Logger,
) -> Any:
    """Fit a single scan using the band-appropriate fitting routine.
    Derives scan geometry from OFFSET, FNBW, and HPBW, dispatches to 
    single-beam or dual-beam fitting based on band, and raises an error 
    for unsupported band values.
    """

    try:
        x = row["OFFSET"]
        fnbw = row["FNBW"] / 2.0
        hpbw = row["HPBW"] / 2.0
    except KeyError as exc:
        raise KeyError(f"Missing required key for fitting: {exc}") from exc

    if band in {"L", "S", "CM", "KU", "K"}:
        return fit_scan(x, y, band, fnbw, hpbw, False, log, out_path, "", "",paths)

    if band == "C":
        return fit_scan_db(x, y, band, fnbw, hpbw, False, log, out_path, "", "", 0.55,paths)

    if band == "X":
        return fit_scan_db(x, y, band, fnbw, hpbw, False, log, out_path, "", "", 0.60,paths)

    raise ValueError(f"Invalid band type: {band}")


def _populate_fit_fields(
    row: Dict[str, Any],
    scan: Any,
    pol_key: str,
    band: str,
    log: logging.Logger,
    args:argparse.Namespace
) -> None:
    """
    Write fit results into row fields that are currently None.
    """

    try:
        del row["ALT1"]
    except:
        pass
    
    try:
        del row["ALT2"]
    except:
        pass
    
    try:
        del row['UISER_LONG']
    except:
        pass
    
    for field, current in list(row.items()):
        # print('--> ',field,current)
        
        if current is not None:
            continue

        # print(current);sys.exit()
        # Dual beam fields for C/X.
        if band in {"C", "X"}:
            # print(f"{pol_key}BRMS", scan.baseline_rms, field)
            # print('==>',field,current, pol_key)#; sys.exit()
            if field == f"{pol_key}RMS":
                row[field] = scan.clean_rms
            elif field == f"{pol_key}BSLOPE":
                try:
                    row[field] = scan.baseline_coeffs[0]
                except (IndexError, TypeError, AttributeError):
                    row[field] = None
            elif field == f"{pol_key}BRMS":
                # print(field,scan.baseline_rms);sys.exit()
                row[field] = scan.baseline_rms
            elif field == f"{pol_key}FLAG":
                row[field] = scan.flag

            elif field == f"A{pol_key}TA":
                row[field] = scan.ata_peak
                # print(field,row[field])
            elif field == f"A{pol_key}TAERR":
                row[field] = scan.ata_peak_err
                
            elif field == f"A{pol_key}TAPEAKLOC":
                row[field] = scan.apeak_loc_index
            elif field == f"A{pol_key}S2N":
                row[field] = sig_to_noise(scan.ata_peak, scan.baseline_residuals, log)
            elif field == f'A{pol_key}QC':
                try:
                    ok = scan.qc.is_bad
                    flag = scan.qc.flag
                    msg = scan.qc.reasons
                except (AttributeError, TypeError):
                    ok = False
                    flag = scan.flag
                    msg = scan.message
                qc={'is_bad':ok, 'flag':flag, 'message':msg}
                row[field] = json.dumps(to_jsonable(qc), ensure_ascii=False)

            elif field == f"B{pol_key}TA":
                row[field] = scan.bta_peak
            elif field == f"B{pol_key}TAERR":
                row[field] = scan.bta_peak_err
            elif field == f"B{pol_key}TAPEAKLOC":
                row[field] = scan.bpeak_loc_index
            elif field == f"B{pol_key}S2N":
                row[field] = sig_to_noise(scan.bta_peak, scan.baseline_residuals, log)
            elif field == f'B{pol_key}QC':
                try:
                    ok = scan.qc.is_bad
                    flag = scan.qc.flag
                    msg = scan.qc.reasons
                except (AttributeError, TypeError):
                    ok = False
                    flag = scan.flag
                    msg = scan.message
                qc={'is_bad':ok, 'flag':flag, 'message':msg}
                row[field] = json.dumps(to_jsonable(qc), ensure_ascii=False)

            # print('<-- ',field,current,row[field])
            # continue


        # Single beam fields.
        if field == f"{pol_key}RMS":
            row[field] = scan.clean_rms
        elif field == f"{pol_key}BSLOPE":
            try:
                row[field] = scan.baseline_coeffs[0]
            except (IndexError, TypeError, AttributeError):
                row[field] = None
        elif field == f"{pol_key}BRMS":
            row[field] = scan.baseline_rms
        elif field == f"{pol_key}FLAG":
            row[field] = scan.flag
        elif field == f"{pol_key}TA":
            row[field] = scan.ta_peak
        elif field == f"{pol_key}TAERR":
            row[field] = scan.ta_peak_err
        elif field == f"{pol_key}TAPEAKLOC":
            row[field] = scan.peak_loc_index
        elif field == f"{pol_key}S2N":
            row[field] = sig_to_noise(scan.ta_peak, scan.baseline_residual, log)
        elif field == f'{pol_key}QC':
            qc={'ok':scan.qc.ok, 'flag':scan.qc.flag, 'message':scan.qc.message, 'metrics':scan.qc.metrics}
            row[field] = json.dumps(to_jsonable(qc), ensure_ascii=False)


def _populate_pointing_single_beam(row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Single beam pointing uses S, N, O triplet per pol.
    Writes PC and corrected ON TA for the ON position only.
    """
    for pol in ["L", "R"]:
        tas: List[float] = []
        for pos in ["S", "N", "O"]:
            tas.append(row.get(f"{pos}{pol}TA"))
            tas.append(row.get(f"{pos}{pol}TAERR"))

        pc = calibrate_pointing_corrected_ta(
            tas[0], tas[1],
            tas[2], tas[3],
            tas[4], tas[5],
            log,
            row,
        )

        on_pos = "O"
        row[f"{on_pos}{pol}PC"] = pc.pc
        row[f"C{on_pos}{pol}TA"] = pc.ta_corr
        row[f"C{on_pos}{pol}TAERR"] = pc.ta_corr_err
        

def _populate_pointing_dual_beam(row: Dict[str, Any], log: logging.Logger) -> None:
    """
    Dual beam pointing uses b in {A,B} and S, N, O triplet per pol.
    Writes PC and corrected ON TA for the ON position only.
    """
    for beam in ["A", "B"]:
        for pol in ["L", "R"]:
            tas: List[float] = []
            for pos in ["S", "N", "O"]:
                tas.append(row.get(f"{beam}{pos}{pol}TA"))
                tas.append(row.get(f"{beam}{pos}{pol}TAERR"))

            pc = calibrate_pointing_corrected_ta(
                tas[0], tas[1],
                tas[2], tas[3],
                tas[4], tas[5],
                log,
                row,
            )

            on_pos = "O"
            row[f"{beam}{on_pos}{pol}PC"] = pc.pc
            row[f"{beam}C{on_pos}{pol}TA"] = pc.ta_corr
            row[f"{beam}C{on_pos}{pol}TAERR"] = pc.ta_corr_err


def _tag_from_data_key(key: str) -> str:
    """Derive a scan tag from a data key string.
    Maps ZC, HPNZ, and HPSZ data keys to on-source, north, or south scan 
    tags and raises an error for unsupported formats.
    """
    # print(key);sys.exit()
    if "ZC" in key:
        return f"O{key.split('_')[1]}"
    if "HPNZ" in key:
        return f"N{key.split('_')[1]}"
    if "HPSZ" in key:
        return f"S{key.split('_')[1]}"
    raise ValueError(f"Unrecognized DATA key format: {key}")


def _plot_base_path(
        row: Mapping[str, Any], 
        src: str, 
        fname: str, 
        paths: ProjectPaths) -> str:
    """Build and ensure the base path for scan plot output.
    Creates the source and frequency-specific plot directory and returns the 
    full file path for the plot.
    """
    # print('here')
    # print(row["CENTFREQ"])
    centfreq_mhz = int(row["CENTFREQ"])
    # print(paths.plots_dir )
    # print(src )
    # print(str(centfreq_mhz) )
    plot_path_dir = paths.plots_dir / src / str(centfreq_mhz) 
    os.makedirs(plot_path_dir, exist_ok=True)

    return str(plot_path_dir/ fname)


def populate_row(
        file_data: Sequence[Dict[str, Any]],
        band: str,
        paths:ProjectPaths,
        log: logging.Logger,
        args:argparse.Namespace,
    ) -> Dict[str, Any]:
    """
    Run fitting per DATA column and populate derived fields back 
    into the row dict. Returns the updated row (last row in 
    file_data, consistent with existing behavior).
    """
    
    # print('In')
    band = band.upper()
    # print('In-',band)
    for row in file_data:
        if row.get("SCAN_ERROR") is not None:
            # Skip fitting if scan extraction failed; keep header-level fields only.
            log.warning("Skipping fitting due to SCAN_ERROR: %s", row["SCAN_ERROR"])
            continue
        # accommodate the new QC feature
        if band=="C" or band == "X":
            for b in ["A","B"]:
                for s in ["N","S","O"]:
                    for p in ["L","R"]:
                        row[f'{b}{s}{p}QC']=None
        else:
            if band == "L" or band=="S":
                for p in ["L","R"]:
                    row[f"O{p}QC"]=None
            else:
                for s in ["N","S","O"]:
                    for p in ["L","R"]:
                        row[f'{s}{p}QC']=None
                    
        # process data 
        data_keys = [k for k in row.keys() if "DATA" in k]
        for key in data_keys:
            # print(row)
            # print(key)
            value = row[key]
            # print('---',key,row[key])
            tag = _tag_from_data_key(key)
            pol_key = tag[:2]
            # print(pol_key) ;sys.exit()
            fname_stub = f"{row['FILENAME'][:18]}_{pol_key}"
            src = str(row.get("OBJECT") or "UNKNOWN").replace(" ", "")#;sys.exit()
            out_path = _plot_base_path(row, src, fname_stub, paths)
            # print(row)
            # print('here'); sys.exit()

            scan = _fit_one_scan(row, value, band, out_path, paths, log)#;print('here')
            # print(row);sys.exit()
            _populate_fit_fields(row=row, scan=scan, pol_key=pol_key, band=band, log=log,args=args)
            
            del scan

    # print('In>')
    # print(row)
    # sys.exit()
    if band in {"CM", "KU", "K"}:
        _populate_pointing_single_beam(row, log)

    if band in {"X", "C"}:
        _populate_pointing_dual_beam(row, log)
    # print('In*')
    # cleanup
    # clear_diagnostics_dir(DIAGNOSTICS_DIRNAME,log)
    
    # print('In=')
    return row
    
