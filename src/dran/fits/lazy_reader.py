# =========================================================================== #
# File: lazy_reader.py                                                        #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
from dran.fits.backends import FitsBackendHandle, open_fits_handle
from dran.fits.types import HduSummary
# =========================================================================== #


class LazyFITSReader:
    """
    Lazy FITS reader.

    Responsibilities:
    - Open and close a FITS file.
    - Provide header access immediately.
    - Load HDU data only when requested.
    - Offer HDU summaries without forcing data reads.
    """

    def __init__(
        self,
        path: Union[str, Path],
        *,
        memmap: bool = True,
        cache_data: bool = True,
    ) -> None:
        if not str(path):
            raise ValueError("path must not be empty")

        self.path: Path = Path(path)
        self.memmap: bool = memmap
        self.cache_data: bool = cache_data

        self._handle: Optional[FitsBackendHandle] = None
        self._data_cache: Dict[int, Any] = {}

    def __enter__(self) -> "LazyFITSReader":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def handle(self) -> FitsBackendHandle:
        if self._handle is None:
            raise RuntimeError("FITS file not opened")
        return self._handle

    def open(self) -> None:
        if self._handle is not None:
            self.close()
        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} not found")
        self._handle = open_fits_handle(self.path, memmap=self.memmap)
        self._data_cache.clear()

    def close(self) -> None:
        self._data_cache.clear()
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def clear_cache(self) -> None:
        self._data_cache.clear()

    def hdu_count(self) -> int:
        return len(self.handle)

    def get_info(self):
        self.handle.get_info()

    def get_header(self, index: int) -> Mapping[str, Any]:
        return self.handle.get_header(index)

    def get_data(self, index: int) -> Any:
        if self.cache_data and index in self._data_cache:
            return self._data_cache[index]

        data = self.handle.get_data(index)

        if self.cache_data:
            self._data_cache[index] = data

        return data

    def list_hdus(self) -> List[HduSummary]:
        out: List[HduSummary] = []

        for i in range(self.hdu_count()):
            hdr = self.get_header(i)
            inferred = self._infer_shape_from_header(hdr)
            if inferred is None:
                shape_value = ""
            else:
                shape_value = "x".join(str(v) for v in inferred)
            out.append(
                {
                    "index": i,
                    "extname": self.handle.get_hdu_name(i),
                    "type": self.handle.get_hdu_type_name(i),
                    "rows":inferred[0] if inferred else '',
                    "cols":inferred[1] if inferred else '',
                    "shape": shape_value,
                    "has_data": inferred is not None,
                }
            )

        return out

    @staticmethod
    def _infer_shape_from_header(header: Mapping[str, Any]) -> Optional[Tuple[int, ...]]:
        naxis = header.get("NAXIS", None)
        if not isinstance(naxis, int) or naxis == 0:
            return None

        xtension = str(header.get("XTENSION", "")).strip().upper()

        if xtension in {"BINTABLE", "TABLE"}:
            nrows = header.get("NAXIS2", None)
            ncols = header.get("TFIELDS", None)
            if isinstance(nrows, int) and isinstance(ncols, int):
                return (nrows, ncols)
            if isinstance(nrows, int):
                return (nrows,)
            return None

        dims: List[int] = []
        for k in range(1, naxis + 1):
            key = f"NAXIS{k}"
            val = header.get(key, None)
            if not isinstance(val, int):
                return None
            dims.append(val)

        return tuple(reversed(dims))
