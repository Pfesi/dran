# =========================================================================== #
# File: sqlite_repository.py                                                  #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import sqlite3
from typing import Any, Mapping, Optional
from .sqlite_schema import _quote_ident
from .sqlite_types import blob_to_array, normalize_for_storage
# =========================================================================== #


def insert_dict(
    conn: sqlite3.Connection,
    table: str,
    item: Mapping[str, Any],
) -> int:
    """
    Insert a dict into table and return inserted row id.
    """
    keys = list(item.keys())
    placeholders = ", ".join("?" for _ in keys)
    col_list = ", ".join(_quote_ident(k) for k in keys)

    vals = [normalize_for_storage(item[k]) for k in keys]

    # cur=conn.execute(f'PRAGMA table_info("{table}")')
    # existing_keys=[row[1] for row in cur.fetchall()]
    # print(existing_keys, keys,len(existing_keys),len(keys))
    cursor = conn.execute(
        f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders});',
        vals,
    )
    return int(cursor.lastrowid)

def fetch_row(
    conn: sqlite3.Connection,
    table: str,
    row_id: int,
) -> dict[str, Any]:
    """
    Fetch a row and reconstruct arrays from BLOBs where possible.
    """
    cursor = conn.execute(f'SELECT * FROM "{table}" WHERE id = ?;', (row_id,))
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Row not found")

    col_names = [d[0] for d in cursor.description]
    data = dict(zip(col_names, row))

    for key, value in data.items():
        if isinstance(value, bytes):
            try:
                data[key] = blob_to_array(value)
            except Exception:
                pass

    return data

def get_existing_keys(
    conn: sqlite3.Connection,
    table: str,
    key: str,
) -> set[Any]:
    """
    Load all existing values of a key into a set for fast membership checks.
    """
    cursor = conn.execute(f'SELECT "{key}" FROM "{table}"')
    return {row[0] for row in cursor.fetchall()}

def save_record(
    conn: sqlite3.Connection,
    table: str,
    item: Mapping[str, Any],
    *,
    create_table_fn: Optional[callable] = None,
) -> int:
    """
    Insert one record. Returns row id.

    create_table_fn is optional and lets callers ensure schema before insert.
    """
    if create_table_fn is not None:
        create_table_fn(conn, table, item)

    return insert_dict(conn, table, item)
