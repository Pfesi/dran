# =========================================================================== #
# File: invalid_path_registry.py                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from pathlib import Path
from typing import Set
import logging
from dran.config.paths import ProjectPaths
# =========================================================================== #


def load_invalid_paths(paths:ProjectPaths,
                       log: logging.Logger) -> Set[str]:
    """
    Load previously recorded invalid paths from disk.

    Returns an empty set if the log file does not exist.
    """
    log.debug(f"Loading invalid path registry from: {paths.invalid_files_path}")

    if not paths.invalid_files_path.exists():
        return set()

    with paths.invalid_files_path.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def load_symlink_paths(
    paths: ProjectPaths,
    log: logging.Logger,
) -> Set[str]:
    """
    Load previously recorded symlink paths from disk.
    """
    log.debug(f"Loading symlink registry from: {paths.symlinks_path}")

    if not paths.symlinks_path.exists():
        return set()

    with paths.symlinks_path.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}
    
    
def append_invalid_path(path: Path, 
                        paths:ProjectPaths,
                        log: logging.Logger) -> None:
    """
    Append a path to the invalid path registry on disk.

    Creates parent directories for the registry file if needed.
    """

    paths.invalid_files_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.invalid_files_path.open("a", encoding="utf-8") as f:
        f.write(f"{path}\n")

    log.debug(f'Appended invalid path "{path}" to {paths.invalid_files_path}')


def append_symlink_path(
    path: Path,
    paths: ProjectPaths,
    log: logging.Logger,
) -> None:
    """
    Append a symlink path to the symlink registry on disk.
    """
    paths.symlinks_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.symlinks_path.open("a", encoding="utf-8") as f:
        f.write(f"{path}\n")

    log.debug(f'Appended symlink path "{path}" to {paths.symlinks_path}')

def record_invalid_path_once(path: Path, 
                             paths:ProjectPaths,
                             log: logging.Logger,  
                             reason: str) -> None:
    """
    Record an invalid path only once.

    If the path is already present, nothing is appended.
    """

    path_key = str(path)
    existing = load_invalid_paths(paths,log)

    if path_key in existing:
        log.debug(f"Invalid path already recorded: {path}")
        return

    log.warning(f"{reason}. Path: {path}")
    append_invalid_path(path, paths, log)

def record_symlink_path_once(
    path: Path,
    paths: ProjectPaths,
    log: logging.Logger,
) -> None:
    """
    Record a symlink path only once in the symlink registry.
    """
    path_key = str(path)
    existing = load_symlink_paths(paths, log)

    if path_key in existing:
        log.debug(f"Symlink path already recorded: {path}")
        return

    log.info(f"Symlink detected: {path}")
    append_symlink_path(path, paths, log)

def _validate_symlink(fits_path: Path, 
                      paths: ProjectPaths, 
                      log: logging.Logger) -> bool:
    """
    Record symlinks and skip broken ones.
    Returns True if the path is safe to process.
    """
    fits_path=Path(fits_path)
    if not fits_path.is_symlink():
        return True

    record_symlink_path_once(fits_path, paths, log)
    try:
        fits_path.resolve(strict=True)
    except FileNotFoundError:
        record_invalid_path_once(fits_path, paths, log, "broken symlink")
        return False
    return True