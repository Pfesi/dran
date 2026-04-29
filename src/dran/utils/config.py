# =========================================================================== #
# File: utils/config.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from dataclasses import dataclass
import logging
import sys
from pathlib import Path
from typing import Optional
# =|========================================================================= #


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

  
@dataclass(frozen=True)
class ProjectPaths:
    workdir: Path
    db_path: Path
    log_path: Path
    invalid_files_path: Path
    symlinks_path: Path
    diagnostics_dir: Path
    plots_dir: Path


# class ObservationPathError(ValueError):
#     pass


class ObservationPathError(Exception):
    """Raised when an observation path cannot be parsed."""
    pass

