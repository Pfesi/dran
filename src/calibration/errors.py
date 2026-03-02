# =========================================================================== #
# File: errors.py                                                             #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


class CalibrationError(Exception):
    """Base exception for calibration failures."""


class MissingResourceError(CalibrationError):
    """Raised when a required packaged resource is missing."""


class UnsupportedFrontendError(CalibrationError):
    """Raised when a frontend/backend type is not supported."""


class EphemerisDateOutOfRangeError(CalibrationError):
    """Raised when an ephemeris table does not cover the requested date."""


class InvalidObservationDateError(CalibrationError):
    """Raised when an observation date string is invalid or cannot be parsed."""
