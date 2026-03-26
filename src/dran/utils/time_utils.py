# =========================================================================== #
# File: time_utils.py                                                         #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from datetime import date, datetime, timedelta
import re
# =========================================================================== #


# --------------------------------------------------------------------------- #
# Module-level constants
# --------------------------------------------------------------------------- #
_DOY_TIMESTAMP_RE = re.compile(
    r"^(?P<year>\d{4})d(?P<doy>\d{3})_(?P<hour>\d{2})h(?P<minute>\d{2})m(?P<second>\d{2})s$"
)


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _validate_doy(year: int, doy: int) -> None:
    max_doy = 366 if _is_leap_year(year) else 365
    if doy < 1 or doy > max_doy:
        raise ValueError(f"DOY must be in 1..{max_doy} for year {year}.")


def doy_to_date(year: int, doy: int) -> date:
    """
    Convert day-of-year to a calendar date.

    Args:
        year: Four-digit year, for example 2024.
        doy: Day of year, starting at 1.

    Returns:
        datetime.date instance.
    """
    
    _validate_doy(year, doy)
    return date(year, 1, 1) + timedelta(days=doy - 1)


def parse_doy_timestamp(value: str) -> datetime:
    """
    Parse a timestamp in the form YYYYdDOY_HHhMMmSSs.

    Example input:
        2023d281_00h01m59s

    Returns:
        datetime.datetime instance in UTC-like naive time.
    """
    
    match = _DOY_TIMESTAMP_RE.match(value)
    if not match:
        raise ValueError("Invalid format. Expected YYYYdDOY_HHhMMmSSs")

    year = int(match.group("year"))
    doy = int(match.group("doy"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))

    _validate_doy(year, doy)
    if not (0 <= hour <= 23):
        raise ValueError("Hour must be in 0..23.")
    if not (0 <= minute <= 59):
        raise ValueError("Minute must be in 0..59.")
    if not (0 <= second <= 59):
        raise ValueError("Second must be in 0..59.")

    base_date = date(year, 1, 1) + timedelta(days=doy - 1)

    return datetime(
        year=base_date.year,
        month=base_date.month,
        day=base_date.day,
        hour=hour,
        minute=minute,
        second=second,
    )
