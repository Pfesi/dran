# =========================================================================== #
# File: paths.py                                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import (
    DB_NAME,LOG_FILENAME,INVALID_FILES_FILENAME,SYMLINKS_FILENAME,
    DIAGNOSTICS_DIRNAME, PLOTS_DIRNAME,
)
# =========================================================================== #


@dataclass(frozen=True)
class ProjectPaths:
    workdir: Path
    db_path: Path
    log_path: Path
    invalid_files_path: Path
    symlinks_path: Path
    diagnostics_dir: Path
    plots_dir: Path


def build_paths(workdir: Path) -> ProjectPaths:
    wd = workdir.expanduser().resolve()
    return ProjectPaths(
        workdir=wd,
        db_path=wd / DB_NAME,
        log_path=wd / LOG_FILENAME,
        invalid_files_path=wd / INVALID_FILES_FILENAME,
        symlinks_path=wd / SYMLINKS_FILENAME,
        diagnostics_dir=wd / DIAGNOSTICS_DIRNAME,
        plots_dir=wd / PLOTS_DIRNAME,
    )
