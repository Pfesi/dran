# =========================================================================== #
# File: dispatcher.py                                                         #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import sys
import numpy as np
from pathlib import Path
from typing import Any, Dict, List
import os
import sys
import argparse
from dran.config.paths import ProjectPaths
from dran.storage.sqlite_connection import get_connection
from dran.fits.observation_extractor import extract_observation
from dran.utils.fs import clear_diagnostics_dir, compute_file_hash
from dran.utils.invalid_path_registry import (
    record_invalid_path_once
)
from dran.utils.paths import (
    parse_source_frequency_band_from_path_if_folder,
    resolve_existing_path,
)
from dran.storage.db_introspection import (
    _ensure_and_insert,
    record_exists, 
    ensure_processed_files_table,
    processed_file_exists_by_path,
    processed_file_hashes_by_size,
    insert_processed_file,
)
from dran.fits.processing_fit import populate_row
from dran.utils.invalid_path_registry import _validate_symlink
from dran.fits.path_resolver import parse_observation_path
from dran.utils.frequency_utils import get_band_from_frequency

# =|========================================================================= #


def process_fits_path(
    root_path: Path,
    threads: int,
    log: logging.Logger,
    paths: ProjectPaths,
    args:argparse.Namespace,
) -> List[Dict[str, Any]]:
    """
    Dispatch processing for a single FITS file or a directory of FITS files.
    Returns extracted FITS records. Directory results are concatenated.
    """

    resolved = resolve_existing_path(root_path, log, paths)
    
    if resolved is None:
        raise ValueError("root_path is None")

    if resolved.is_file():
        _process_single_file(resolved, paths, log,args)
        return

    if resolved.is_dir():
        _process_directory(resolved, log,paths, args)
        return 

    raise ValueError(f"Invalid path type: {resolved}")


def _should_skip_by_registry(
    fits_path: Path,
    paths: ProjectPaths,
    log: logging.Logger,
) -> tuple[bool, str | None, int, float]:
    """
    Hybrid de-duplication:
    - Skip if FILEPATH is already registered.
    - If file_size matches existing entries, compute hash and skip if hash exists.
    Returns (skip, file_hash_or_none, file_size, file_mtime).
    """
    stat = fits_path.stat()
    file_size = stat.st_size
    file_mtime = stat.st_mtime

    conn = get_connection(paths.db_path, log)
    try:
        ensure_processed_files_table(conn)

        if processed_file_exists_by_path(conn, str(fits_path)):
            return True, None, file_size, file_mtime

        known_hashes = set(processed_file_hashes_by_size(conn, file_size))
        file_hash: str | None = None
        if known_hashes:
            file_hash = compute_file_hash(fits_path)
            if file_hash in known_hashes:
                return True, file_hash, file_size, file_mtime

        return False, file_hash, file_size, file_mtime
    finally:
        conn.close()


def _record_processed_file(
    fits_path: Path,
    paths: ProjectPaths,
    log: logging.Logger,
    args:argparse.Namespace,
    *,
    file_hash: str | None,
    file_size: int,
    file_mtime: float,
) -> None:
    
    """Persist processed file metadata for path-independent de-duplication."""
    
    if file_hash is None:
        file_hash = compute_file_hash(fits_path)

    conn = get_connection(paths.db_path, log)
    try:
        insert_processed_file(
            conn,
            file_hash=file_hash,
            file_size=file_size,
            file_mtime=file_mtime,
            filepath=str(fits_path),
            filename=fits_path.name
        )
    finally:
        conn.close()


def _process_single_file(
        fits_path: Path, 
        paths: ProjectPaths, 
        log: logging.Logger,
        args: argparse.Namespace) -> List[Dict[str, Any]]:
    
    
    fits_path=Path(fits_path)
  
    if not _validate_symlink(fits_path, paths, log):
        return []

    if fits_path.stat().st_size == 0:
        record_invalid_path_once(fits_path,paths, log, "empty file")
        return []
    

                        
    p=parse_observation_path(fits_path)
    
    # print(p,p.band_folder) 

    if p.band_folder==None:
        print(">> ",fits_path, paths, p.band_folder)

        record = extract_observation(fits_path, paths, p.band_folder, log)
        print(record)
        
        src=record["OBJECT"]
        band=record["BAND"]
        freq_mhz=int(record["CENTFREQ"])
        table_name = f"{src}_{freq_mhz}".upper()
                  
        conn = get_connection(paths.db_path, log)
        
        already_done = record_exists(conn, table_name, "FILEPATH", str(fits_path))
        conn.close()
        
        if already_done:
            log.debug("Skipping already processed file: %s", fits_path)
            return []

        skip, file_hash, file_size, file_mtime = _should_skip_by_registry(
            fits_path, paths, log
        )
        
        # print("skip: ", skip)
        if skip:
            log.debug("Skipping duplicate file by registry: %s", fits_path)
            return []
        
        
        record = extract_observation(fits_path, paths, band, log)
        # print(record);sys.exit()
                  
        scan = [record]
        row = populate_row(scan, band, paths, log,args)
        # print('here*')
        disallowed_keys: set[str] = {"UISER_LONG", 
                                    "GAIN1", "GAIN2",
                                    "ALTGAIN1","ALTGAIN2","ALTGAIN3"}  
        row = {k: v for k, v in row.items() if k not in disallowed_keys}

        # print('here')
        _ensure_and_insert(table_name,row,paths,log)
        _record_processed_file(
            fits_path,
            paths,
            log,
            args,
            file_hash=file_hash,
            file_size=file_size,
            file_mtime=file_mtime,
        )
        clear_diagnostics_dir(paths.diagnostics_dir, log)
        del row
        del scan
        
    else:
        # print('p: ',p);sys.exit()
        src=p.source
        freq_mhz=int(p.frequency)
        # print(src,freq_mhz)
        # sys.exit()
        band=get_band_from_frequency(freq_mhz,log)
        band=band.upper()
        table_name = f"{src}_{freq_mhz}".upper()

        # print(table_name)
        conn = get_connection(paths.db_path, log)
        
        already_done = record_exists(conn, table_name, "FILEPATH", str(fits_path))
        conn.close()

        # print('out', already_done)
        if already_done:
            log.debug("Skipping already processed file: %s", fits_path)
            return []

        skip, file_hash, file_size, file_mtime = _should_skip_by_registry(
            fits_path, paths, log
        )
        
        # print("skip: ", skip)
        if skip:
            log.debug("Skipping duplicate file by registry: %s", fits_path)
            return []
        
        # print(">> ",fits_path, paths, band)

        record = extract_observation(fits_path, paths, band, log)
        # print('here',band);sys.exit()
        scan = [record]
        row = populate_row(scan, band, paths, log,args)
        # print('here*')
        disallowed_keys: set[str] = {"UISER_LONG", 
                                    "GAIN1", "GAIN2",
                                    "ALTGAIN1","ALTGAIN2","ALTGAIN3"}  
        row = {k: v for k, v in row.items() if k not in disallowed_keys}

        # print('here')
        _ensure_and_insert(table_name,row,paths,log)
        _record_processed_file(
            fits_path,
            paths,
            log,
            args,
            file_hash=file_hash,
            file_size=file_size,
            file_mtime=file_mtime,
        )
        clear_diagnostics_dir(paths.diagnostics_dir, log)
        del row
        del scan
        
        # return scan


def _process_directory(root_dir: Path, 
                       log: logging.Logger, 
                       paths: ProjectPaths,
                       args: argparse.Namespace,
                       ) -> List[Dict[str, Any]]:
    
    results: List[Dict[str, Any]] = []


    for dirpath, dirnames, files in os.walk(root_dir):
        base = Path(dirpath)

        if len(files) > 0:
            parent_files=[]
            for file in files:
                parent_files.append(base / file )

            if len(files)==1:
                if files[0]=='.DS_Store':
                    continue
            
            fits_files = sorted([path for path in parent_files if path.name.lower().endswith(".fits")])
            # print(fits_files);sys.exit()
            if fits_files:
                try:
                    src, _freq_mhz, band = parse_source_frequency_band_from_path_if_folder(base, log)
                except Exception as exc:
                    log.warning("Skipping directory %s: %s", base, exc)
                    continue
                # De-dup is handled by the processed_files registry (path + hash).
                paths_to_process = fits_files
                paths_to_process.reverse()
                
                if len(paths_to_process) > 0:
                    log.info('*'*80)
                    log.info('File stats')
                    log.info("*"*80)
                    log.info("Directory: %s", base)
                    log.info("Total files: %s", len(parent_files))
                    log.info("New files: %s", len(paths_to_process))
                    log.info('-'*80)
                    log.debug('\n')
                    
                    for fits_path in paths_to_process:
                        if '.DS_Store' in str(fits_path):
                            continue

                        if not _validate_symlink(fits_path, paths, log):
                            continue

                        if fits_path.stat().st_size == 0:
                            record_invalid_path_once(fits_path,paths, log, "empty file")
                            continue

                        skip, file_hash, file_size, file_mtime = _should_skip_by_registry(
                            fits_path, paths, log
                        )
                        if skip:
                            log.debug("Skipping duplicate file by registry: %s", fits_path)
                            continue

                        log.info(f"\nWorking on path: {fits_path}")
                        record = extract_observation(fits_path, paths,band, log)#;sys.exit()
                        scan = [record]
                        results.append(record)

                        if src==None:
                            src=record["OBJECT"]
                        if band==None:
                            band=record["BAND"]
                        if _freq_mhz==None:
                            _freq_mhz=int(record["CENTFREQ"])
                        
                        # print(src, _freq_mhz,band);sys.exit()
                        row = populate_row(scan, band, paths,log,args)#;sys.exit()
                        disallowed_keys: set[str] = {"UISER_LONG", 
                                                     "GAIN1", "GAIN2",
                                                     "ALTGAIN1","ALTGAIN2","ALTGAIN3"}  # example
                        row = {k: v for k, v in row.items() if k not in disallowed_keys}

                        # print(row['OBJECT'].replace(' ','')); sys.exit()
                        try:
                            src=row['OBJECT'].replace(' ','').upper()
                        except:
                            pass
                        table_name=f'{src}_{int(_freq_mhz)}'.upper()
                        _ensure_and_insert(table_name,row,paths,log)
                        _record_processed_file(
                            fits_path,
                            paths,
                            log,
                            args,
                            file_hash=file_hash,
                            file_size=file_size,
                            file_mtime=file_mtime,
                            
                        )
                        clear_diagnostics_dir(paths.diagnostics_dir, log)
                        
                        del row
                        del scan#; sys.exit()
                else:
                    log.info(f"Directory {base} has {len(paths_to_process)} files, skipping process")
            else:
                log.info(f"Directory {base} has no `    fits files, skipping process")
            
    
    return #results
