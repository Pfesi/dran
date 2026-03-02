
from pathlib import Path
import logging
from src.config.paths import ProjectPaths
from src.utils.invalid_path_registry import (
    record_invalid_path_once,
    record_symlink_path_once,
)

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