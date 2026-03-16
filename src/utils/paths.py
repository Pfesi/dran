# =========================================================================== #
# File: paths.py                                                              #                          
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from pathlib import Path
from typing import Tuple
import logging
import sys
from .invalid_path_registry import record_invalid_path_once
from src.config.paths import ProjectPaths
from .frequency_utils import get_band_from_frequency
from src.fits.path_resolver import parse_observation_path, parse_observation_path_if_folder
# =========================================================================== #

    
def resolve_existing_path(
    path: Path,
    log: logging.Logger,
    paths: ProjectPaths | None = None,
) -> Path:
    """
    Resolve a filesystem path strictly.

    Returns:
        Resolved absolute path.

    Raises:
        FileNotFoundError: If the path does not exist.
        OSError: If the path cannot be resolved.
    """
    resolved_path = Path(path)
    log.debug("Resolving path: %s", resolved_path)

    try:
        return resolved_path.resolve(strict=True)
    except FileNotFoundError:
        if paths is not None:
            record_invalid_path_once(
                resolved_path,
                paths,
                log,
                reason="Path does not exist or is a broken symlink",
            )
        else:
            log.warning("Path does not exist or is a broken symlink: %s", resolved_path)
        raise
    except OSError:
        log.info('Path "%s" cannot be resolved', resolved_path)
        raise
    
def resolve_existing_path_without_logger(path: Path) -> Path:
    """
    Resolve a filesystem path strictly.

    Returns:
        Resolved absolute path.
    """
    # Non-strict resolve: expands user and normalizes without checking existence.
    resolved_path = Path(path)
    return resolved_path.expanduser().resolve(strict=False)
    
    
def remove_symlinks_in_place(
    paths: list[Path],
    log: logging.Logger | None = None,
) -> None:
    """
    Remove all symlinks from the list in place.
    """
    if log is not None:
        log.debug("Removing symlinks from path list")
    paths[:] = [p for p in paths if not p.is_symlink()]


def parse_source_frequency_band_from_path_if_file(
    path: Path,
    log: logging.Logger,
) -> Tuple[str, int, str]:
    """
    Parse (source_name, frequency_mhz, band) from a FITS file path.

    Assumes a directory layout like:
        .../<SOURCE_NAME>/<FREQUENCY_MHZ>/<file>.fits

    Returns:
        (source_name_upper, frequency_mhz, band)
    """
    
    path_obj = Path(path)
    print('here')
    print(path_obj)
    x=parse_observation_path(path_obj)
    print('\n>>>>',x.category,x.source,x.frequency,x.filename,x.full_path)
    # log.debug('what')
    log.debug("Parsing source, frequency, band from path: %s", path_obj)
    # sys.exit()
   
    try:
        source_name = x.source
        frequency_mhz = int(x.frequency)
        band = get_band_from_frequency(frequency_mhz, log)

        log.info("*"*80)
        log.info("Source parameters")
        log.info("*"*80)
        log.info(f"Target: {source_name}")
        log.info(f"Frequency: {frequency_mhz} MHz")
        log.info(f"Band: {band}")
        log.info("*"*80)
        print()

        return source_name, frequency_mhz, band
    except (IndexError, ValueError, AttributeError) as exc:
        log.error("Failed to parse path structure for %s. Error: %s", path_obj, exc)
        raise ValueError(f"Invalid observation path structure: {path_obj}") from exc


def parse_source_frequency_band_from_path_if_folder(
    path: Path,
    log: logging.Logger,
) -> Tuple[str, int, str]:
    """
    Parse (source_name, frequency_mhz, band) from a FITS file path.

    Assumes a directory layout like:
        .../<SOURCE_NAME>/<FREQUENCY_MHZ>/<file>.fits

    Returns:
        (source_name_upper, frequency_mhz, band)
    """
    
    path_obj = Path(path)
    log.debug("Parsing source, frequency, band from path: %s", path_obj)

    x=parse_observation_path_if_folder(path_obj)
    # print(x)
    # print('\n>>>>',x.source, x.frequency, x.band_folder)#;sys.exit()
    
    
        

    try:
        source_name:str = x.source.upper() #path_obj.parents[0].name.upper()
        frequency_mhz:int = x.frequency #int(path_obj.name)
        band:str = get_band_from_frequency(frequency_mhz, log)
        # print(source_name, frequency_mhz,band);sys.exit()

        return source_name, frequency_mhz, band
    except (IndexError, ValueError, AttributeError) as exc:

        try:
            frequency_mhz, source_name=parse_source_directory_path(str(path))

            source_name:str = source_name.upper()
            frequency_mhz:int = int(frequency_mhz)
            band:str = get_band_from_frequency(frequency_mhz, log)
            return source_name, frequency_mhz, band
        except:
            log.error("Failed to parse path structure for %s. Error: %s", path_obj, exc)
            raise ValueError(f"Invalid observation path structure: {path_obj}") from exc


def parse_source_directory_path(path: str | Path) -> Tuple[int, str]:
    """
    Extract frequency and source name from a directory path.

    Expected structure:
        .../<SOURCE>/<FREQ>/
        .../<SOURCE>/*_<FREQ>/

    Returns:
        (frequency, source)
    """

    path_obj = Path(path)
    parts = path_obj.parts

    if len(parts) < 2:
        raise ValueError("Path does not contain enough segments")

    # Source is the parent directory name
    source = parts[-2].upper()

    # Frequency is derived from the last path segment
    freq_part = parts[-1]
    try:
        frequency = int(freq_part)
    except ValueError:
        try:
            frequency = int(freq_part.split("_")[-1])
        except ValueError as exc:
            raise ValueError(f"Cannot extract frequency from '{freq_part}'") from exc

    return frequency, source
