# =========================================================================== #
# File: db_introspection.py                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import re
import sqlite3
from pathlib import Path
from typing import Iterable
import logging
from typing import Any, Dict, List
from src.config.paths import ProjectPaths
from src.storage.sqlite_schema import ensure_table_from_dict
from src.storage.sqlite_connection import get_connection
from src.storage.sqlite_repository import insert_dict
# =========================================================================== #


_TABLE_FREQ_SUFFIX = re.compile(r"^(?P<prefix>.+)_(?P<freq>\d+)$")
_PROCESSED_FILES_TABLE = "processed_files"

def get_table_names(database_path: str) -> List[str]:
    """
    Return a sorted list of user-defined table names
    from the given SQLite database file.

    :param database_path: Path to the SQLite .db file
    :return: List of table names
    """
    query: str = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """

    with sqlite3.connect(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

    # Extract table names from returned tuples
    return [row[0] for row in rows]

def list_tables_in_frequency_range(
    db_path: Path,
    start_mhz: int,
    end_mhz: int,
) -> list[tuple[str, int]]:
    """
    Return (table_name, freq_mhz) for tables named <prefix>_<freq_mhz>
    where freq_mhz is within [start_mhz, end_mhz].
    """
    conn = sqlite3.connect(str(db_path))
    try:
        return list_tables_in_frequency_range_conn(conn, start_mhz, end_mhz)
    finally:
        conn.close()


def list_tables_in_frequency_range_conn(
    conn: sqlite3.Connection,
    start_mhz: int,
    end_mhz: int,
) -> list[tuple[str, int]]:
    rows = conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table';"
    ).fetchall()

    matches: list[tuple[str, int]] = []
    for (name,) in rows:
        m = _TABLE_FREQ_SUFFIX.match(name)
        if not m:
            continue

        freq_mhz = int(m.group("freq"))
        if start_mhz <= freq_mhz <= end_mhz:
            matches.append((name, freq_mhz))

    matches.sort(key=lambda x: (x[1], x[0]))
    return matches


def fetch_existing_file_basenames_and_paths(
        path_to_db:Path,
        tables: Iterable[str],
        log,
        filepath_field: str = "FILEPATH",
) -> tuple[set[str], dict[str, str]]:
    """
    Return:
    - basenames: set of file basenames found in FILEPATH columns
    - basename_to_path: dict mapping basename -> first seen stored path

    Notes:
    - Identifier quoting is used for table and column names.
    - NULL or empty values are skipped.
    """
    if filepath_field != "FILEPATH":
        raise ValueError("Only filepath_field='FILEPATH' is supported.")

    basenames: set[str] = set()
    
    conn = get_connection(path_to_db, log)
    try:
        for table in tables:
            try:
                cursor = conn.execute(
                    f'SELECT "{filepath_field}" FROM "{table}";'
                )
            except sqlite3.Error:
                continue

            for (filepath,) in cursor:
                if not filepath:
                    continue

                basename = Path(filepath).name
                basenames.add(basename)

                # if basename not in basename_to_path:
                #     basename_to_path[basename] = str(filepath)
    finally:
        conn.close()

    return basenames#, basename_to_path


def record_exists(
        conn: sqlite3.Connection, 
        table: str, 
        key_field: str, 
        key_value: Any
        ) -> bool:
    """
    Fast existence check using an indexed lookup (UNIQUE field).

    Returns True if a record exists, else False.
    """
    
    try:
        cursor = conn.execute(
            f'SELECT 1 FROM "{table}" WHERE "{key_field}" = ? LIMIT 1;',
            (key_value,),
        )
    except:
        print('>>>> Failed')
        # check if table exists
        # names=get_table_names
        query: str = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """
        cursor= conn.execute(query)
        rows = cursor.fetchall()
        # Extract table names from returned tuples
        tables= [row[0] for row in rows]
        print('=====',table in tables)
        
        
    print('found: ',cursor.fetchone())
    return cursor.fetchone() is not None


def _ensure_and_insert(
    table_name: str,
    row: Dict[str, Any],
    paths:ProjectPaths,
    log: logging.Logger,
) -> None:
    
    """Ensure a SQLite table exists and insert a row safely.
    Opens a database connection, creates the table schema from the row if 
    needed, inserts the row, logs duplicates on integrity errors, and always closes the connection.
    """
    # print('****',paths, paths.db_path,)
    conn = get_connection(paths.db_path, log)
    ensure_table_from_dict(conn, table_name, row)
    row_id = insert_dict(conn, table_name, row)
    try:
        row_id = insert_dict(conn, table_name, row)
        log.debug("Inserted id=%s into %s", row_id, table_name)
    except sqlite3.IntegrityError:
        log.debug("Row already exists in %s. Skipping.", table_name)
    finally:
        conn.close()


def ensure_processed_files_table(conn: sqlite3.Connection) -> None:
    """
    Ensure a small registry table exists for processed files.

    This enables fast de-duplication across path changes and symlinks.
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{_PROCESSED_FILES_TABLE}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT UNIQUE,
            file_size INTEGER,
            file_mtime REAL,
            filepath TEXT,
            filename TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )
    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_processed_files_size ON "{_PROCESSED_FILES_TABLE}" (file_size);'
    )
    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_processed_files_path ON "{_PROCESSED_FILES_TABLE}" (filepath);'
    )


def processed_file_exists_by_path(conn: sqlite3.Connection, filepath: str) -> bool:
    ensure_processed_files_table(conn)
    cursor = conn.execute(
        f'SELECT 1 FROM "{_PROCESSED_FILES_TABLE}" WHERE filepath = ? LIMIT 1;',
        (filepath,),
    )
    return cursor.fetchone() is not None


def processed_file_hashes_by_size(conn: sqlite3.Connection, file_size: int) -> List[str]:
    ensure_processed_files_table(conn)
    cursor = conn.execute(
        f'SELECT file_hash FROM "{_PROCESSED_FILES_TABLE}" WHERE file_size = ?;',
        (file_size,),
    )
    return [row[0] for row in cursor.fetchall() if row and row[0]]


def insert_processed_file(
    conn: sqlite3.Connection,
    *,
    file_hash: str,
    file_size: int,
    file_mtime: float,
    filepath: str,
    filename: str
) -> None:
    ensure_processed_files_table(conn)
    conn.execute(
        f"""
        INSERT OR IGNORE INTO "{_PROCESSED_FILES_TABLE}"
        (file_hash, file_size, file_mtime, filepath, filename)
        VALUES (?, ?, ?, ?, ?);
        """,
        (file_hash, file_size, file_mtime, filepath, filename),
    )
