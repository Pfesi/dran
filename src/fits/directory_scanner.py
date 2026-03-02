# =========================================================================== #
# File: directory_scanner.py                                                  #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from itertools import groupby
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple
from src.utils.fs import ensure_directory_exists
from src.utils.paths import remove_symlinks_in_place
# =|========================================================================= #


def scan_fits_directory(
    fits_path_dir: Path,
    pattern: str = "*.fits",
    recursive: bool = True,
    log: logging.Logger | None = None,
) -> List[Path]:
    """
    Collect FITS file paths from a directory.

    Returns sorted file paths. Sorting groups by parent directory first, 
    then name.
    """

    ensure_directory_exists(fits_path_dir, log)
    resolved_dir = Path(fits_path_dir).expanduser().resolve()

    files = list(resolved_dir.rglob(pattern)) if recursive else \
        list(resolved_dir.glob(pattern))
    files.sort(key=lambda p: (str(p.parent), p.name))
    return files


def group_files_by_parent(
    files: Iterable[Path]
    ) -> Iterator[Tuple[Path, List[Path]]]:
    """
    Yield (parent_dir, files_in_parent_dir) pairs.

    Input ordering matters. Provide paths sorted by parent then name.
    """

    sorted_files = list(files)
    sorted_files.sort(key=lambda p: (str(p.parent), p.name))

    for parent, group in groupby(sorted_files, key=lambda p: p.parent):
        yield parent, list(group)


def filter_symlinks(
    files: List[Path], 
    log: logging.Logger | None = None
    ) -> List[Path]:
    """
    Remove symlinks from a list of paths and return the filtered list.

    Uses remove_symlinks_in_place from src.utils.paths for consistent behavior.
    """

    filtered = list(files)
    remove_symlinks_in_place(filtered, log)

    if log is not None:
        log.debug(f"Symlink filter applied. Remaining files: {len(filtered)}")

    return filtered
