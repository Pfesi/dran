# =========================================================================== #
# File: sqlite_Schema.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #

# Library imports
# --------------------------------------------------------------------------- #
import sqlite3
from typing import Any, Mapping
import numpy as np
from dran.storage.sqlite_types import normalize_for_schema
# =========================================================================== #


# def _quote_ident(name: str) -> str:
#     return f'"{name.replace("\"", "\"\"")}"'

def _quote_ident(name: str) -> str:
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def infer_sqlite_type(value: Any) -> str:
    """
    Infer an SQLite column type from a sample value.

    Uses:
    - BLOB for non-scalar NumPy arrays
    - REAL for int/float scalars
    - TEXT for everything else
    """
    if isinstance(value, np.ndarray) and value.shape != ():
        return "BLOB"

    v = normalize_for_schema(value)
    if isinstance(v, (int, float)):
        return "REAL"

    return "TEXT"


def ensure_table_from_dict(
    conn: sqlite3.Connection,
    table: str,
    sample: Mapping[str, Any],
    unique_field: str = "FILENAME",
) -> None:
    """
    Create a table if it does not exist.

    Column names are taken from sample keys.
    Each column type is inferred from sample values.

    unique_field is used as a UNIQUE constraint if it exists in sample.
    """
    columns = [
        f"{_quote_ident(key)} {infer_sqlite_type(value)}"
        for key, value in sample.items()
    ]
    # print(columns)
    schema = ", ".join(columns)

    if unique_field in sample:
        unique_sql = f", UNIQUE ({_quote_ident(unique_field)})"
    else:
        unique_sql = ""

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{table}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {schema}
            {unique_sql}
        );
        """
    )
