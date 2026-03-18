# =========================================================================== #
# File: atmos_frontend_dispatch.py                                            #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from typing import Any, Dict
from src.calibration.errors import UnsupportedFrontendError
from src.calibration.atmosphere.atmos_models import (
    apply_atmospheric_absorption_db,
    apply_atmospheric_absorption_sb,
    apply_atmospheric_penetration_1p3s,
    apply_atmospheric_penetration_2p5s,
)
from src.calibration.planets.planet_jupiter_calibration import (
    apply_jupiter_atmospheric_calibration)
# =========================================================================== #


def dispatch_atmospheric_correction(row: Dict[str, Any], 
                                    log: logging.Logger) -> None:
    """
    Dispatch to the correct atmospheric model based on EXTNAME.

    This function mutates row in place.
    """
    extname = str(row.get("EXTNAME", "")).strip()

    if extname == "02.5S":
        apply_atmospheric_penetration_2p5s(row, log)
        return

    if extname == "01.3S":
        apply_atmospheric_penetration_1p3s(row, log)

        obj = str(row.get("OBJECT", "")).strip().upper()
        if obj == "JUPITER":
            apply_jupiter_atmospheric_calibration(row, log)
        return

    if "13.0S" in extname or "18.0S" in extname:
        apply_atmospheric_absorption_sb(row, log)
        return

    if "04.5S" in extname:
        # Placeholder for future implementation.
        log.warning("Atmospheric calibration not implemented for EXTNAME=%s", extname)
        return

    if "D" in extname:
        apply_atmospheric_absorption_db(row, log)
        return

    raise UnsupportedFrontendError(
        f"Atmospheric calibration not implemented for EXTNAME={extname}"
    )
