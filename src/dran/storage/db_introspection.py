# =========================================================================== #
# File: db_introspection.py                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
# import re
# from typing import Iterable
import sqlite3
from pathlib import Path
import logging
import os
import numpy as np
from typing import Any, Dict, List
import pandas as pd
from dran.utils.fs import ProjectPaths
from dran.storage.sqlite_schema import ensure_table_from_dict
from dran.storage.sqlite_connection import get_connection
from dran.storage.sqlite_repository import insert_dict


# =========================================================================== #


# _TABLE_FREQ_SUFFIX = re.compile(r"^(?P<prefix>.+)_(?P<freq>\d+)$")
_PROCESSED_FILES_TABLE = "processed_files"

def get_table_names(database_path: Path) -> List[str]:
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


def get_table_from_db(dbPath: str, tableName: str) -> pd.DataFrame:
    """
    """
    
    with sqlite3.connect(dbPath) as cnx:
        df = pd.read_sql_query(f"SELECT * FROM '{tableName}'", cnx)
    return df

def prep_data(dataframe: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Preprocess the data in the DataFrame for analysis.

    Args:
        dataframe (pd.DataFrame): The input DataFrame containing observational data.
        source_name (str): The name of the source being processed.

    Returns:
        pd.DataFrame: The processed DataFrame.
    """

    # --- Remove all data from Marisa's gain observations
    dataframe=dataframe.loc[~dataframe.FILENAME.str.contains('marisa')]

    # --- Sort the DataFrame by filename
    dataframe.sort_values(by='FILENAME', inplace=True)

    # --- Parse observation dates
    dataframe = parse_observation_dates(dataframe)

    # --- Identify columns to convert to numeric (excluding metadata columns)
    exclude_keywords = [
            'FILE', 'FRONT', 'OBJ', 'SRC', 'OBS', 'PRO', 'TELE', 'HDU', 'id', 'DATE',
            'UPGR', 'TYPE', 'COOR', 'EQU', 'RADEC', 'SCAND', 'BMO', 'DICH', 'PHAS',
            'POINTI', 'TIME', 'INSTRU', 'INSTFL', 'time', 'HABM'
        ]
    dataframe = convert_to_numeric(dataframe, exclude_keywords)

    # Add source name to the DataFrame
    dataframe['FILES'] = dataframe['FILENAME'].str[:18]
    dataframe['OBJECT'] = source_name

    # Ensure all error columns have positive values
    dataframe = ensure_positive_errors(dataframe)
    return dataframe

def parse_time(timeCol: str) -> str:
    """
    """
    
    if 'T' in timeCol:
        return timeCol.split('T')[0]
    else:
        return timeCol.split(' ')[0]
    
def parse_observation_dates(df: pd.DataFrame,form='m') -> pd.DataFrame:
    """
    Parse the observation date column into a datetime format.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with parsed dates.
    """
    
    df['time'] = df['OBSDATE'].astype(str)
    df['OBSDATE'] = df['time'].apply(parse_time)
    df['OBSDATE'] = pd.to_datetime(df['OBSDATE']).dt.date
    df['OBSDATE'] = pd.to_datetime(df['OBSDATE'], format=f"%Y-%{form}-%d")
    return df

def convert_to_numeric(dataframe: pd.DataFrame, exclude_keywords: List[str]) -> pd.DataFrame:
    """
    Convert columns to numeric, excluding those containing specific keywords.

    Args:
        dataframe (pd.DataFrame): The input DataFrame.
        exclude_keywords (List[str]): Keywords to exclude from numeric conversion.

    Returns:
        pd.DataFrame: The DataFrame with numeric columns.
    """

    colList=list(dataframe.columns)
    floatList = [col for col in colList if not any(excl in col for excl in exclude_keywords)]
    # --- Rather than fail, we might want 'pandas' to be considered a missing/bad numeric value. We can coerce invalid values to NaN as follows using the errors keyword argument:
    dataframe[floatList] = dataframe[floatList].apply(pd.to_numeric, errors='coerce')

    return dataframe

def ensure_positive_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all error columns have positive values.

    Args:
        dataframe (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with positive error values.
    """
    err_cols = df.filter(like='ERR').columns
    df[err_cols] = df[err_cols].map(make_positive)

    return df

def make_positive(value):
    """
    Ensure the input value is positive and convert it to a float. If the value is invalid or negative, return NaN.

    Args:
        value (Any): The input value to process.

    Returns:
        float: The positive float value or NaN if the value is invalid or negative.
    """
    # Check if the value is None or an empty string
    if value is None or value == '':
        return np.nan

    try:
        # Convert the value to a float
        numeric_value = float(value)
        # Return the value if it is non-negative, otherwise return NaN
        return numeric_value if numeric_value >= 0 else np.nan
    except (ValueError, TypeError):
        # Handle invalid values (e.g., non-numeric strings)
        return np.nan

def get_data_from_db(processed_db_path,DB_PATH: Path, 
                     freq: int,
                     table_name: str,
                     src: str,
                     log=''):
       
    # Check if processed database exists
    db_found = os.path.isfile(processed_db_path)

    if db_found:
        print(f'Database {src}.db already exists, appending new files to database')
            
        with sqlite3.connect(DB_PATH) as cnx:
            df_original = pd.read_sql_query(f"SELECT * FROM {table_name}", cnx)
            df_original.sort_values(by='FILENAME', inplace=True)
            original_files = list(df_original['FILENAME'])

        #     print('Reading from processed db')
        with sqlite3.connect(processed_db_path) as cnx1:
            
            # print('\n',src_name, processed_db_path,'\n')
            try:
                if freq=='2280':
                    df_processed = get_2ghz_data(table_name, cnx1)
                else:
                    df_processed = pd.read_sql_query(f"SELECT * FROM {table_name}", cnx1)
                df_processed.sort_values(by='FILENAME', inplace=True)
                processed_files = list(df_processed['FILENAME'])

                # Identify new files
                new_files = [file for file in original_files if file not in processed_files]

                # Combine processed and missing data
                df_missing = df_original[~df_original.FILENAME.isin(processed_files)]
                print(f'Adding {len(df_missing)} new files to processed db')
                print(len(new_files), len(processed_files), len(df_original), len(df_missing))
                    
                df = pd.concat([df_processed, df_missing])
                # dbs[table_name] = df

            except: # sqlite3.OperationalError:
                print(f'\nTable {table_name} not found in processed db, processing from scratch')
                # dbs[table_name] = df_original
                df= df_original
                
    else:
        if log:
            print(f'\nDatabase {src}.db does not exist, processing from scratch')
        with sqlite3.connect(DB_PATH) as cnx:
            if freq=='2280':
                df=get_2ghz_data(table_name, cnx)
            else:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", cnx)
            # dbs[table_name] = df
        return df            

def get_2ghz_data(table_name: str, cnx):
    if table_name.split('_')[-1].startswith('2280'):
        df_original = pd.read_sql_query(f"SELECT * FROM {table_name}", cnx)
        try:
            df1=pd.read_sql_query(f"SELECT * FROM {table_name.replace('2280','2270')}", cnx)
            df_original=pd.concat([df_original,df1])
        except:
            pass
        df_original.sort_values(by='FILENAME', inplace=True)
    else:
        df_original = pd.read_sql_query(f"SELECT * FROM {table_name}", cnx)
        df_original.sort_values(by='FILENAME', inplace=True)
    return df
   



# def list_tables_in_frequency_range(
#     db_path: Path,
#     start_mhz: int,
#     end_mhz: int,
# ) -> list[tuple[str, int]]:
#     """
#     Return (table_name, freq_mhz) for tables named <prefix>_<freq_mhz>
#     where freq_mhz is within [start_mhz, end_mhz].
#     """
#     conn = sqlite3.connect(str(db_path))
#     try:
#         return list_tables_in_frequency_range_conn(conn, start_mhz, end_mhz)
#     finally:
#         conn.close()


# def list_tables_in_frequency_range_conn(
#     conn: sqlite3.Connection,
#     start_mhz: int,
#     end_mhz: int,
# ) -> list[tuple[str, int]]:
#     rows = conn.execute(
#         "SELECT name FROM sqlite_schema WHERE type='table';"
#     ).fetchall()

#     matches: list[tuple[str, int]] = []
#     for (name,) in rows:
#         m = _TABLE_FREQ_SUFFIX.match(name)
#         if not m:
#             continue

#         freq_mhz = int(m.group("freq"))
#         if start_mhz <= freq_mhz <= end_mhz:
#             matches.append((name, freq_mhz))

#     matches.sort(key=lambda x: (x[1], x[0]))
#     return matches


# def fetch_existing_file_basenames_and_paths(
#         path_to_db:Path,
#         tables: Iterable[str],
#         log,
#         filepath_field: str = "FILEPATH",
# ) -> tuple[set[str], dict[str, str]]:
#     """
#     Return:
#     - basenames: set of file basenames found in FILEPATH columns
#     - basename_to_path: dict mapping basename -> first seen stored path

#     Notes:
#     - Identifier quoting is used for table and column names.
#     - NULL or empty values are skipped.
#     """
#     if filepath_field != "FILEPATH":
#         raise ValueError("Only filepath_field='FILEPATH' is supported.")

#     basenames: set[str] = set()
    
#     conn = get_connection(path_to_db, log)
#     try:
#         for table in tables:
#             table=table.upper()
#             try:
#                 cursor = conn.execute(
#                     f'SELECT "{filepath_field}" FROM "{table}";'
#                 )
#             except sqlite3.Error:
#                 continue

#             for (filepath,) in cursor:
#                 if not filepath:
#                     continue

#                 basename = Path(filepath).name
#                 basenames.add(basename)

#                 # if basename not in basename_to_path:
#                 #     basename_to_path[basename] = str(filepath)
#     finally:
#         conn.close()

#     return basenames#, basename_to_path


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
    
    table=table.upper()
    
    try:
        cursor = conn.execute(
            f'SELECT 1 FROM "{table}" WHERE "{key_field}" = ? LIMIT 1;',
            (key_value,),
        )
        # print('oi')
        return cursor.fetchone()
    except:
        print('>>>> No record of this observation')
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
        
        print(f"Table : {table} not found")
            
        return None


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
    table_name=table_name.upper()
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
