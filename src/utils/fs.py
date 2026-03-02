# =========================================================================== #
# File: fs.py                                                                 #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from pathlib import Path
from typing import Iterable
import logging
import shutil
import hashlib
# =|========================================================================= #


def ensure_directory_exists(base_folder: Path, log: logging.Logger | None = None) -> None:
    """
    Ensure the given path exists and is a directory.
    """
    
    folder = Path(base_folder)

    if not folder.exists():
        if log is not None:
            log.error(f"Folder not found: {folder}")
        raise FileNotFoundError(str(folder))

    if not folder.is_dir():
        if log is not None:
            log.error(f"Not a folder: {folder}")
        raise NotADirectoryError(str(folder))
    
    
def ensure_output_directories(
    paths: Iterable[Path],
    log: logging.Logger,
    *,
    overwrite_if_contains: str = "diagnostic",
) -> None:
    """
    Ensure required output directories exist.

    Default behavior:
    - If the directory path contains the token "diagnostic", it is recreated.
    - All other directories are created if missing.
    """

    for folder in paths:
        folder_path = Path(folder)

        if overwrite_if_contains and overwrite_if_contains in str(folder_path):
            recreate_dir(folder_path, log)
        else:
            create_dir(folder_path, log)
            

def recreate_dir(folder_path: Path, log: logging.Logger) -> None:
    """
    Recreate a directory.

    If the directory already exists, it is removed with all contents, then
    recreated (including parents).
    """
    
    folder_path = Path(folder_path)

    if folder_path.exists():
        shutil.rmtree(folder_path)

    folder_path.mkdir(parents=True, exist_ok=True)
    log.debug("Recreated directory: %s", folder_path)
    

def create_dir(folder_path: Path, log: logging.Logger) -> None:
    """
    Ensure a directory exists.

    Creates parent directories as needed. If it already exists, it is left
    unchanged.
    """
    
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    log.debug("Ensured directory exists: %s", folder_path)
    

def clear_diagnostics_dir(path: Path, log: logging.Logger) -> None:
    """Remove all files and subdirectories from a diagnostics directory.
    Safely deletes directory contents if the path exists. Logs a warning for 
    any item that cannot be removed.
    """
    
    if not path.exists():
        return
    if not path.is_dir():
        log.warning("Diagnostics path is not a directory: %s", path)
        return

    for item in path.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as exc:
            log.warning("Failed to delete %s: %s", item, exc)


def compute_file_hash(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Compute a SHA-256 hash for a file by streaming its contents."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
