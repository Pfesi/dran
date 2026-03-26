# =========================================================================== #
# File: jpl_horizons_table.py                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Any
from dran.calibration.resource_utils import get_jpl_results
from dran.calibration.errors import MissingResourceError
# =========================================================================== #


def load_jpl_horizons_table(log: logging.Logger) -> Any:
    """
    Load the packaged JPL Horizons results table.

    Returns:
        Any: Typically a pandas DataFrame as returned by get_jpl_results().

    Raises:
        MissingResourceError: If the packaged resource is missing.
    """

    try:
        return get_jpl_results(log)
    except Exception as exc:
        raise MissingResourceError(
            "The 'nasa_jpl_data.txt' resource is not available in the distribution."
        ) from exc
