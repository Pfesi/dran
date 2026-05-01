# =========================================================================== #
# File: init_processes.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =>========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from typing import Callable, Dict
import argparse
from pathlib import Path

from dran.utils.fs import build_paths
from dran.config.logging import setup_logger, logging, load_prog
from dran.config.constants import (
    PROJECT_NAME, LOG_FILENAME, PLOTS_DIRNAME, DIAGNOSTICS_DIRNAME,
)
from dran.utils.fs import ensure_output_directories
from dran.pipelines.fits_processing import run_fits_processing
from dran.pipelines.gui_processing import run_gui_processing
from dran.pipelines.web_processing import run_web_processing
from dran.pipelines.docs_processing import run_docs_processing
from dran.pipelines.analysis_processing import run_analysis_processing
# =========================================================================== #


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
    """
    Main entry point for the application run.
    
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


    def run_server(args,paths,log):
        # try:
            from dran.server.server_processing import run_server_side_processing
            run_server_side_processing(args,paths,log)
        # except:
        #     print("Server access not Implemented. Contact author.")
        
    dispatch: Dict[str, Callable[[argparse.Namespace, Path, logging.Logger], None]] = {
        "auto": run_fits_processing,
        "gui": run_gui_processing,
        "web": run_web_processing,
        "docs": run_docs_processing,
        "anal": run_analysis_processing,
        "serve": run_server,
    }

    if args.mode == "auto":
        load_prog(PROJECT_NAME, log)
    else:
        pass

    dispatch[args.mode](args=args, paths=paths, log=log)
