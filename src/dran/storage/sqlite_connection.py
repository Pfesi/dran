# =========================================================================== #
# File: sqlite_connection.py                                                  #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =>========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import sqlite3
from pathlib import Path
from typing import Optional
import logging
# =========================================================================== #



def get_connection(db_path: Path, log: Optional[logging.Logger] = None) -> sqlite3.Connection:
    """
    Open a SQLite connection with pragmatic defaults for local workloads.

    Settings applied:
    - WAL mode for better concurrent reads/writes
    - synchronous NORMAL for balanced durability and speed
    - busy_timeout to reduce "database is locked" failures
    """
    conn = sqlite3.connect(
        db_path,
        timeout=30.0,
        isolation_level=None,  # autocommit
    )

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    if log is not None:
        log.debug("Opened SQLite connection: %s", db_path)

    return conn
