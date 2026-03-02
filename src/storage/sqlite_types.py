# =========================================================================== #
# File: sqlite_types.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import io
from typing import Any
import numpy as np
# =========================================================================== #


def array_to_blob(arr: np.ndarray) -> bytes:
    """
    Encode a NumPy array as bytes for SQLite storage.

    Uses np.save into an in-memory buffer, preserving dtype and shape.
    """
    buf = io.BytesIO()
    np.save(buf, arr, allow_pickle=False)
    return buf.getvalue()


def blob_to_array(blob: bytes) -> np.ndarray:
    """
    Decode stored bytes back into a NumPy array.
    """
    buf = io.BytesIO(blob)
    return np.load(buf, allow_pickle=False)


def normalize_for_schema(value: Any) -> Any:
    """
    Normalize values for schema inference.

    SQLite column typing is coarse. This converts NumPy scalars and 0-D arrays
    into Python scalars so the type checks behave as expected.
    """
    if isinstance(value, np.ndarray) and value.shape == ():
        return value.item()

    if isinstance(value, np.generic):
        return value.item()

    return value


def normalize_for_storage(value: Any) -> Any:
    """
    Prepare a value for SQLite insertion.

    Rules:
    - 0-D NumPy arrays -> Python scalar
    - NumPy scalars -> Python scalar
    - N-D NumPy arrays (shape != ()) -> BLOB
    - Everything else unchanged
    """
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return value.item()
        return array_to_blob(value)

    if isinstance(value, np.generic):
        return value.item()

    return value
