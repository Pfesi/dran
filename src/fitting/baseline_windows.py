# =========================================================================== #
# File: baseline_windows.py                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
from itertools import chain
from typing import List, Tuple
import numpy as np
# =========================================================================== #


def filter_invalid_minima(
    local_max_positions: np.ndarray,
    local_min_positions: np.ndarray,
    max_points: int,
    log: logging.Logger,
) -> np.ndarray:
    """
    Removes minima that fall inside max windows.
    """
    points_to_delete: List[int] = []
    half = int(max_points / 2)

    for mx in local_max_positions:
        window = np.arange(mx - half, mx + half, 1)
        for mn in local_min_positions:
            if mn in window:
                points_to_delete.append(int(mn))

    if points_to_delete:
        keep = [mn for mn in local_min_positions.tolist() if int(mn) not in points_to_delete]
        local_min_positions = np.asarray(keep, dtype=int)

    log.debug("Validated minima. mins=%s maxs=%s", local_min_positions, local_max_positions)
    return local_min_positions


def build_baseline_windows(
    x: np.ndarray,
    left_mins: list[int],
    right_mins: list[int],
    left_hpbw_idx: int,
    right_hpbw_idx: int,
    left_fnbw_idx: int,
    right_fnbw_idx: int | None,
    max_points: int,
    log: logging.Logger,
) -> Tuple[np.ndarray, int]:
    """
    Builds baseline sample indices by selecting blocks around minima.
    Returns:
        (indices_sorted_unique, flag)
    """
    max_points = min(max_points, len(x))
    half = int(max_points / 2)
    windows: list[np.ndarray] = []
    flag = 0

    # Left side
    if left_mins:
        for j in left_mins:
            j = int(j)
            if j <= half:
                windows.append(np.arange(0, max_points, 1))
                flag = 8
            elif j >= left_hpbw_idx:
                windows.append(np.arange(0, max_points, 1))
                flag = 8
            else:
                start = max(0, j - half)
                end = min(len(x), j + half)
                windows.append(np.arange(start, end, 1))
    else:
        windows.append(np.arange(0, max_points, 1))
        flag = 10

    # Right side
    if right_mins:
        for j in right_mins:
            j = int(j)
            if j >= len(x) - 1:
                flag = 10
                continue
            if j >= len(x) - half:
                a = abs(len(x) - abs(len(x) - j) - half)
                start = max(0, int(a))
                windows.append(np.arange(start, len(x), 1))
                flag = 9
            else:
                start = max(0, j - half)
                end = min(len(x), j + half)
                windows.append(np.arange(start, end, 1))
    else:
        start = max(0, len(x) - max_points)
        windows.append(np.arange(start, len(x), 1))
        flag = 11

    indices = sorted(set(chain.from_iterable([w.tolist() for w in windows])))
    return np.asarray(indices, dtype=int), flag
