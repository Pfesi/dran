# =========================================================================== #
# File: hdu_rules.py                                                          #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from typing import List
# =========================================================================== #


def scan_hdu_indices(hdu_len: int) -> List[int]:
    """
    Return HDU indices that contain scan data based on your known file layouts.

    Existing rules preserved:
    - If HDULEN == 5, scan index is [3]
    - If HDULEN == 7, scan indices are [3, 4, 5]
    - if HDULEN == 6, for older systems, scan indices are [3, 4, 5]

    For unknown HDU lengths, return an empty list.
    """

    if hdu_len == 5:
        return [3]
    if hdu_len == 7 or hdu_len == 6:
        return [3, 4, 5]
    return []
