# =========================================================================== #
# File: fitting/config.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from dataclasses import dataclass
import logging
import sys
from pathlib import Path
from typing import Optional
# =|========================================================================= #

@dataclass(frozen=True)
class DualBeamQCConfig:
    step_sigma_mult: float = 12.0
    step_count_max: int = 6
    max_gap_frac: float = 0.10
    min_points_per_beam: int = 20
    max_edge_frac: float = 0.20
    max_resid_to_baseline_rms: float = 2.5
    min_snr: float = 2.0
    max_amp_ratio: float = 4.0