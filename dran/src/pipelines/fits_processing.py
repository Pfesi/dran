# =========================================================================== #
# File: fits_processing.py                                                    #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Standard library imports
# --------------------------------------------------------------------------- #
import argparse
import logging
from pathlib import Path
from typing import Optional
from src.config.paths import ProjectPaths
from src.fits.dispatcher import process_fits_path
# =========================================================================== #


def run_fits_processing(
    args: argparse.Namespace,
    paths: ProjectPaths,
    log: logging.Logger
    ) -> None:
    """
    Pipeline entry point for FITS processing.

    Responsibilities:
    - validate required CLI args
    - dispatch to FITS processing workflow
    """

    if not hasattr(args, "path") or args.path is None:
        log.critical("Missing required argument: -path")
        raise ValueError("args.path is required")
    
    input_path: Path = args.path

    threads: Optional[int] = getattr(args, "threads", None)

    log.info("Starting FITS processing for: %s", input_path)

    # Collect extracted records (for a file or directory)
    process_fits_path(
        root_path=input_path,
        threads=threads,
        log=log,
        paths=paths,
        args=args
    )
