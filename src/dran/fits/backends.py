# =========================================================================== #
# File: backends.py                                                           #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping,Protocol, runtime_checkable
# =========================================================================== #


@runtime_checkable
class FitsBackendHandle(Protocol):
    """
    Backend handle interface used by FITSReader.

    This keeps FITSReader independent from astropy or fitsio APIs.
    """

    def __len__(self) -> int: ...
    def get_hdu_name(self, index: int) -> str: ...
    def get_hdu_type_name(self, index: int) -> str: ...
    def get_header(self, index: int) -> Mapping[str, Any]: ...
    def get_data(self, index: int) -> Any: ...
    def get_info(self) -> None: ...
    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class BackendSelection:
    name: str


def select_backend() -> BackendSelection:
    """
    Select a FITS backend.

    Preference order:
    1) fitsio
    2) astropy
    """
    try:
        import fitsio  # noqa: F401  # type: ignore
        return BackendSelection(name="fitsio")
    except Exception:
        return BackendSelection(name="astropy")


def open_fits_handle(path: Path, memmap: bool) -> FitsBackendHandle:
    """
    Open a FITS file with the selected backend.

    Parameters
    ----------
    path
        FITS file path.
    memmap
        Used by astropy. fitsio ignores this flag.
    """
    selection = select_backend()
    if selection.name == "fitsio":
        return _FitsioHandle(path=path)
    return _AstropyHandle(path=path, memmap=memmap)


class _AstropyHandle:
    def __init__(self, path: Path, memmap: bool) -> None:
        from astropy.io import fits  # type: ignore

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        self._fits = fits
        self._hdus = fits.open(path, memmap=memmap)
        self.path = path

    def __len__(self) -> int:
        return len(self._hdus)

    def get_hdu_name(self, index: int) -> str:
        hdu = self._hdus[index]
        return str(getattr(hdu, "name", ""))

    def get_hdu_type_name(self, index: int) -> str:
        return type(self._hdus[index]).__name__

    def get_header(self, index: int) -> Mapping[str, Any]:
        return self._hdus[index].header

    def get_info(self) -> None:
        self._fits.info(self.path)

    def get_data(self, index: int) -> Any:
        return self._hdus[index].data
    
    def get_shape(self, index: int) -> Any:
        return self.get_data(index).shape

    def close(self) -> None:
        self._hdus.close()


class _FitsioHandle:
    def __init__(self, path: Path) -> None:
        import fitsio  # type: ignore

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        self._fitsio = fitsio
        self._handle = fitsio.FITS(str(path))

    def __len__(self) -> int:
        return len(self._handle)

    def get_hdu_name(self, index: int) -> str:
        # fitsio has EXTNAME in the header for most HDUs
        header = self.get_header(index)
        name = header.get("EXTNAME")
        return str(name) if name is not None else ""

    def get_hdu_type_name(self, index: int) -> str:
        # fitsio does not expose astropy classes, so infer from header
        header = self.get_header(index)
        xtension = str(header.get("XTENSION", "")).strip().upper()
        if xtension:
            return xtension
        if index == 0:
            return "PRIMARY"
        return "HDU"

    def get_header(self, index: int) -> Mapping[str, Any]:
        return self._handle[index].read_header()

    def get_data(self, index: int) -> Any:
        return self._handle[index].read()

    def get_info(self) -> None:
        self._handle.info()

    def close(self) -> None:
        self._handle.close()
