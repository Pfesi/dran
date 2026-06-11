# =========================================================================== #
# File: sqlite_repository.py                                                  #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import sqlite3
import sys
from typing import Any, Mapping, Optional
from .sqlite_schema import _quote_ident
from .sqlite_types import blob_to_array, normalize_for_storage
# =========================================================================== #

def quote_sqlite_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def column_exists(con: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    quoted_table = quote_sqlite_identifier(table_name)
    cursor = con.execute(f"PRAGMA table_info({quoted_table})")
    existing_columns = [row[1] for row in cursor.fetchall()]
    return column_name in existing_columns

def add_column_if_missing(
    con: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str = "TEXT",
) -> None:
    # with sqlite3.connect(db_path) as con:
        if not column_exists(con, table_name, column_name):
            quoted_table = quote_sqlite_identifier(table_name)
            quoted_column = quote_sqlite_identifier(column_name)

            con.execute(
                f"ALTER TABLE {quoted_table} "
                f"ADD COLUMN {quoted_column} {column_type}"
            )
            con.commit()

            print(f"Added column {column_name} to {table_name}")
            return con.execute(f"SELECT last_insert_rowid()").fetchone()[0]
        else:
            print(f"Column {column_name} already exists in {table_name}")
        # sys.exit()

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
    # # print(existing_keys)
    # print(existing_keys, keys,len(existing_keys),len(keys))

    try:
        cursor = conn.execute(
            f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders});',
            vals,
        )
        return int(cursor.lastrowid)
    
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            raise RuntimeError(f"Table '{table}' does not exist. Consider creating it first.") from e
        elif 'has no column named HPNZ_LCPDATA' in str(e):
            print("Column missing. Consider updating the schema or creating \
                the table with the correct schema.")
            cursor=add_column_if_missing(
                con=conn,
                table_name=table,
                column_name="HPNZ_LCPDATA",
                column_type="BLOB",
            )
            return int(cursor) #.lastrowid)
        elif 'has no column named HPNZ_RCPDATA' in str(e):
            print("Column missing. Consider updating the schema or creating \
                the table with the correct schema.")
            cursor=add_column_if_missing(
                con=conn,
                table_name=table,
                column_name="HPNZ_RCPDATA",
                column_type="BLOB",
            )
            return int(cursor) #.lastrowid)
        elif 'has no column named HPSZ_LCPDATA' in str(e):
            print("Column missing. Consider updating the schema or creating \
                the table with the correct schema.")
            cursor=add_column_if_missing(
                con=conn,
                table_name=table,
                column_name="HPSZ_LCPDATA",
                column_type="BLOB",
            )
            return int(cursor) #.lastrowid)
        elif 'has no column named HPSZ_RCPDATA' in str(e):
            print("Column missing. Consider updating the schema or creating \
                the table with the correct schema.")
            cursor=add_column_if_missing(
                con=conn,
                table_name=table,
                column_name="HPSZ_RCPDATA",
                column_type="BLOB",
            )
            return int(cursor) #.lastrowid)
        else:
            raise

        

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
