# =========================================================================== #
# File: paths.py                                                              #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from pathlib import Path
from typing import Tuple
import sys
# =========================================================================== #


def parse_plot_path(path: str | Path) -> Tuple[str, str, str]:
    """
    Extract source name, frequency, and filename from a plot path.

    Expected structure:
        base / <src_name> / <freq> / <filename>

    Returns:
        (src_name, freq, filename)
    """
    p = Path(path).resolve()
    try:
        src_name = p.parts[-3]
        freq = p.parts[-2]
        filename = p.parts[-1]
    except IndexError as exc:
        raise ValueError(f"Invalid path structure: {path}") from exc

    return src_name, freq, filename
