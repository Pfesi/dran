# =========================================================================== #
# File: fs.py                                                                 #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #

from pathlib import Path
from typing import Iterable, Optional, Tuple
import logging
import shutil
import sys
import hashlib
from typing import Set
from dran.utils.config import (
    ObservationPathError, ProjectPaths,
    ObservationPathParts, ObservationPathPartsFolder)
from dran.config.constants import (
    _WAVELENGTH_BEAM_RE, _WAVELENGTH_ONLY_RE, FREQ_ALIASES,
    DB_NAME,LOG_FILENAME,INVALID_FILES_FILENAME,SYMLINKS_FILENAME,
    DIAGNOSTICS_DIRNAME, PLOTS_DIRNAME
)
from dran.utils.frequency_utils import (
    get_band_from_frequency,_resolve_band_to_frequency_mhz)
# =|========================================================================= #


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
    
    
# def remove_symlinks_in_place(
#     paths: list[Path],
#     log: logging.Logger | None = None,
# ) -> None:
#     """
#     Remove all symlinks from the list in place.
#     """
#     if log is not None:
#         log.debug("Removing symlinks from path list")
#     paths[:] = [p for p in paths if not p.is_symlink()]


# def parse_source_frequency_band_from_path_if_file(
#     path: Path,
#     log: logging.Logger,
# ) -> Tuple[str, int, str]:
#     """
#     Parse (source_name, frequency_mhz, band) from a FITS file path.

#     Assumes a directory layout like:
#         .../<SOURCE_NAME>/<FREQUENCY_MHZ>/<file>.fits

#     Returns:
#         (source_name_upper, frequency_mhz, band)
#     """
    
#     path_obj = Path(path)
#     x=parse_observation_path(path_obj)
#     log.debug("Parsing source, frequency, band from path: %s", path_obj)

   
#     try:
#         source_name = x.source
#         frequency_mhz = int(x.frequency)
#         band = get_band_from_frequency(frequency_mhz, log)

#         log.info("*"*80)
#         log.info("Source parameters")
#         log.info("*"*80)
#         log.info(f"Target: {source_name}")
#         log.info(f"Frequency: {frequency_mhz} MHz")
#         log.info(f"Band: {band}")
#         log.info("*"*80)
#         print()

#         return source_name, frequency_mhz, band
#     except (IndexError, ValueError, AttributeError) as exc:
#         log.error("Failed to parse path structure for %s. Error: %s", path_obj, exc)
#         raise ValueError(f"Invalid observation path structure: {path_obj}") from exc

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

    if x.source==None:
        return x.source, x.frequency, x.band_folder

    try:
        source_name:str = x.source.upper() 
        frequency_mhz:int = x.frequency 
        band:str = get_band_from_frequency(frequency_mhz, log)
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


def parse_plot_path(path: str | Path) -> Tuple[str, str, str]:
    """
    Extract source name, frequency, and filename from a plot path.

    Expected structure:
        base / <src_name> / <freq> / <filename>

    Returns:
        (src_name, freq, filename)
    """
    p = Path(path).resolve()
    try:
        src_name = p.parts[-3]
        freq = p.parts[-2]
        filename = p.parts[-1]
    except IndexError as exc:
        raise ValueError(f"Invalid path structure: {path}") from exc

    return src_name, freq, filename


def resolve_existing_path_without_logger(path: Path) -> Path:
    """
    Resolve a filesystem path strictly.

    Returns:
        Resolved absolute path.
    """
    # Non-strict resolve: expands user and normalizes without checking existence.
    resolved_path = Path(path)
    return resolved_path.expanduser().resolve(strict=False)
    
    
def parse_observation_path(path_str: str) -> ObservationPathParts:
    """
    Parse observation file paths for DRAN.

    Supported layouts:
    data/calibration/3C123/12178/file.fits
    data/calibration/3C123_12178/file.fits
    data/calibration/3C123_13NB/file.fits
    data/calibration/3C123_13NB_dichroic_on/file.fits
    data/calibration/3C123_35/file.fits
    data/calibration/3C123_3.5NB/file.fits
    data/calibration/Jup/file.fits
    """
    p = Path(path_str).expanduser().resolve()
    parts = p.parts

    if "data" not in parts:
        raise ObservationPathError(f"Missing 'data' directory in path: {p}")

    data_idx = parts.index("data")
    rel = parts[data_idx + 1 :]

    # if len(rel) < 3:
    #     raise ObservationPathError(f"Invalid observation path structure: {p}")

    category = rel[0]
    filename = rel[-1]

    # Layout A: data/category/source/frequency/file
    if len(rel) >= 4:
        source = rel[1]
        band = rel[2]

        freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
            band=band,
            source_freq_folder=f"{source}_{band}",
            p=p,
        )

        return ObservationPathParts(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=freq_mhz,
            filename=filename,
            full_path=p,
            wavelength_cm=wavelength_cm,
            beam=beam,
            band_folder=band,
        )

    # Layout B/C: data/category/source_band[_extra_tokens]/file
    source_freq_folder = rel[1]
    if "_" not in source_freq_folder:
        
        if rel[0]=='12GHz_continuum':
                freq="12218"
                wav='2.5'
                bm="NB"
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=rel[1],
                    frequency=freq,
                    filename=rel[-1],
                    full_path=p,
                    wavelength_cm=wav,
                    beam=bm,
                    band_folder="2.5",
                )
                
        elif rel[0]=='22GHz_continuum':
                freq="22040"
                wav='1.3'
                bm="NB"
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=rel[1],
                    frequency=freq,
                    filename=rel[-1],
                    full_path=p,
                    wavelength_cm=wav,
                    beam=bm,
                    band_folder="1.3",
                )
                              
        else:
            try:
                source = rel[1]
                freq_mhz, wavelength_cm, beam = _read_frequency_from_fits_header(p)
                
                return ObservationPathParts(
                    root_data_dir=Path(*parts[: data_idx + 1]),
                    category=category,
                    source=source,
                    frequency=freq_mhz,
                    filename=filename,
                    full_path=p,
                    wavelength_cm=wavelength_cm,
                    beam=beam,
                    band_folder="header_inferred",
                )
            except:
                print('***',source_freq_folder)
                raise ObservationPathError(f"Missing source_<band> pattern: {p}")

    sf_tokens = [t for t in source_freq_folder.split("_") if t]
    if len(sf_tokens) < 2:
        raise ObservationPathError(f"Missing band token in folder '{source_freq_folder}': {p}")

    source = sf_tokens[0]
    candidate_tokens = sf_tokens[1:]

    band_token: Optional[str] = None
    for token in candidate_tokens:
        # Accept first token that looks like either:
        #  - digits (frequency or wavelength-only)
        #  - wavelength+beam (13NB, 3.5WB, etc.)
        #  - decimal wavelength-only (3.5)
        if token.isdigit():
            band_token = token
            break
        if _WAVELENGTH_BEAM_RE.match(token):
            band_token = token
            break
        if _WAVELENGTH_ONLY_RE.match(token):
            band_token = token
            break

    if band_token is None:
        # raise ObservationPathError(
        #     f"Unrecognized band folder in '{source_freq_folder}': {p}"
        # )
        return ObservationPathParts(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=np.nan,
            filename=filename,
            full_path=p,
            wavelength_cm=None,
            beam="",
            band_folder=None,
        )

    freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
        band=band_token,
        source_freq_folder=source_freq_folder,
        p=p,
    )

    return ObservationPathParts(
        root_data_dir=Path(*parts[: data_idx + 1]),
        category=category,
        source=source,
        frequency=freq_mhz,
        filename=filename,
        full_path=p,
        wavelength_cm=wavelength_cm,
        beam=beam,
        band_folder=band_token,
    )
    
    
def parse_observation_path_if_folder(path_str: str) -> ObservationPathPartsFolder:
    """
    Parse observation file paths for DRAN.

    Supported layouts:
    data/calibration/3C123/12178/
    data/calibration/3C123_12178/
    data/calibration/3C123_13NB/
    data/calibration/3C123_13NB_dichroic_on/
    data/calibration/3C123_35/
    data/calibration/3C123_3.5NB/
    data/calibration/3C123/
    data/calibration/Jup/
    """
    
    print(path_str,'\n')
    
    p = Path(path_str).expanduser().resolve()
    parts = p.parts
    # print(parts)
    if "data" not in parts:
        raise ObservationPathError(f"Missing 'data' directory in path: {p}")

    data_idx = parts.index("data")
    rel = parts[data_idx + 1 :]
    print(rel,'\n')
    # if len(rel) < 2:
    #     raise ObservationPathError(f"Invalid observation path structure: {p}")

    category = rel[0]
    foldername = rel[-1]

    if rel[0]==rel[-1]:
        # print('out',Path(*parts[: data_idx + 1]),category,source,freq_mhz,foldername,p,wavelength_cm,beam,band_token)
        return ObservationPathPartsFolder(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=None,
            frequency=None,
            foldername=foldername,
            full_path=p,
            wavelength_cm=None,
            beam=None,
            band_folder=None,
        )
    
    # Layout A: data/category/source/frequency/
    # print(category,foldername,rel,'\n')
    if len(rel) >= 3:
        source = rel[1]
        band = rel[2]

        freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
            band=band,
            source_freq_folder=f"{source}_{band}",
            p=p,
        )

        return ObservationPathPartsFolder(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=source,
            frequency=freq_mhz,
            foldername=foldername,
            full_path=p,
            wavelength_cm=wavelength_cm,
            beam=beam,
            band_folder=band,
        )

    # Layout B/C: data/category/source_band[_extra_tokens]/
    source_freq_folder = rel[1]
    print(source_freq_folder)
    if "_" not in source_freq_folder:
        # raise ObservationPathError(f"Missing source_<band> pattern: {p}")
        print(f"Missing source_<band> pattern: {p}")#;sys.exit()
        return ObservationPathPartsFolder(
            root_data_dir=Path(*parts[: data_idx + 1]),
            category=category,
            source=None,
            frequency=None,
            foldername=foldername,
            full_path=p,
            wavelength_cm=None,
            beam=None,
            band_folder=None,
        )
        
    sf_tokens = [t for t in source_freq_folder.split("_") if t]
    # print(sf_tokens)
    if len(sf_tokens) < 2:
        raise ObservationPathError(f"Missing band token in folder '{source_freq_folder}': {p}")

    source = sf_tokens[0]
    candidate_tokens = sf_tokens[1:]
    # print(candidate_tokens)
    band_token: Optional[str] = None
    for token in candidate_tokens:
        # Accept first token that looks like either:
        #  - digits (frequency or wavelength-only)
        #  - wavelength+beam (13NB, 3.5WB, etc.)
        #  - decimal wavelength-only (3.5)
        if token.isdigit():
            band_token = token
            break
        if _WAVELENGTH_BEAM_RE.match(token):
            band_token = token
            break
        if _WAVELENGTH_ONLY_RE.match(token):
            band_token = token
            break
    # print(band_token)
    if band_token is None:
        raise ObservationPathError(
            f"Unrecognized band folder in '{source_freq_folder}': {p}"
        )

    freq_mhz, wavelength_cm, beam = _resolve_band_to_frequency_mhz(
        band=band_token,
        source_freq_folder=source_freq_folder,
        p=p,
    )
    # print('out',Path(*parts[: data_idx + 1]),category,source,freq_mhz,foldername,p,wavelength_cm,beam,band_token)
    return ObservationPathPartsFolder(
        root_data_dir=Path(*parts[: data_idx + 1]),
        category=category,
        source=source,
        frequency=freq_mhz,
        foldername=foldername,
        full_path=p,
        wavelength_cm=wavelength_cm,
        beam=beam,
        band_folder=band_token,
    )
    
    
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

