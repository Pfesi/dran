# =========================================================================== #
# File: init_processes.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Callable, Dict
import argparse
from pathlib import Path

from src.config.paths import build_paths
from src.config.logging import setup_logger, logging, load_prog
from src.config.constants import (
    PROJECT_NAME, LOG_FILENAME, PLOTS_DIRNAME, DIAGNOSTICS_DIRNAME,
)
from src.utils.fs import ensure_output_directories
from src.pipelines.fits_processing import run_fits_processing
from src.pipelines.gui_processing import run_gui_processing
from src.pipelines.web_processing import run_web_processing
from src.pipelines.docs_processing import run_docs_processing
from src.pipelines.analysis_processing import run_analysis_processing
from src.server.server_processing import run_server_side_processing
# =|========================================================================= #


def init_output_directories(
    workdir: Path,
    log: logging.Logger,
) -> None:
    """Initialize output directories for diagnostics and plots.
    Creates the required subdirectories inside the working directory if they 
    do not exist, and logs the operation.
    """
    
    output_directories = [
        workdir / DIAGNOSTICS_DIRNAME,
        workdir / PLOTS_DIRNAME,
    ]
    ensure_output_directories(output_directories, log)


def run(
    args: argparse.Namespace) -> None:
    """Main entry point for the application run.
    Creates the working directory, configures logging, builds path mappings, 
    initializes output directories, and dispatches execution to the selected 
    processing mode based on the provided arguments.
    """

    Path(args.workdir).mkdir(parents=True, exist_ok=True)
    
    log: logging.Logger = setup_logger(
        debug=args.debug,
        project_name=PROJECT_NAME,
        log_file=args.workdir / LOG_FILENAME,
    )
    
    paths = build_paths(args.workdir)
    init_output_directories(paths.workdir, log)

    dispatch: Dict[str, Callable[[argparse.Namespace, logging.Logger], None]] = {
        "auto": run_fits_processing,
        "gui": run_gui_processing,
        "web": run_web_processing,
        "docs": run_docs_processing,
        "anal": run_analysis_processing,
        "serve": run_server_side_processing,
    }

    if args.mode == "auto":
        load_prog(PROJECT_NAME, log)
    else:
        pass

    dispatch[args.mode](args=args, paths=paths, log=log)
