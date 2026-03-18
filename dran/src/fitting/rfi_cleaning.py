# =========================================================================== #
# File: rfi_cleaning.py                                                       #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import numpy as np
from astropy.stats import sigma_clip
from typing import Sequence, Any
from typing import Optional, Union
from src.fitting.models import (CleanedScan, ResidualFit, 
                                IterativeCleaningResult)
from src.fitting.spline_models import spline_fit_1d
# =========================================================================== #


def clean_rfi_sigma_clip(x: np.ndarray, y: np.ndarray, log: logging.Logger
                         ) -> CleanedScan:
    """
    Sort x, build a spline, sigma-clip residuals, return inliers plus 
    artefacts.
    """
    
    log.debug("RFI cleaning started")

    order = np.argsort(x)
    x_s = x[order]
    y_s = y[order]

    spl = spline_fit_1d(y_s, log=log)
    resid = y_s - spl

    clipped = sigma_clip(resid, sigma=2.5, cenfunc="median", stdfunc="mad_std", maxiters=10)
    mask_inliers = ~clipped.mask

    clean_x = x_s[mask_inliers]
    clean_y = y_s[mask_inliers]

    final_spl = spline_fit_1d(clean_y, log=log)
    res = np.asarray(final_spl - clean_y, dtype=float)
    clipped_rms = float(np.sqrt(np.nanmean(res ** 2)))

    points_deleted = np.where(~mask_inliers)[0]

    return CleanedScan(
        x=clean_x,
        y=clean_y,
        rms=clipped_rms,
        residual=np.asarray(clipped, dtype=float),
        spline_max=float(np.max(final_spl)) if final_spl.size else float("nan"),
        spline=np.asarray(final_spl, dtype=float),
        points_deleted=np.asarray(points_deleted, dtype=int),
        flag=0,
    )


def clean_data(
    x: Union[np.ndarray, Sequence[float]],
    y: Union[np.ndarray, Sequence[float]],
    log: Optional[logging.Logger] = None,
) -> CleanedScan:
    """
    Clean a drift scan using iterative RFI rejection and refitting.

    Pipeline
    1) Spline fit to y
    2) Compute residuals and RMS
    3) Iteratively reject outliers and refit until RMS no longer improves

    Parameters
    ----------
    x, y
        1D arrays of equal length.
    log
        Optional logger.

    Returns
    -------
    CleanedScan
        Container holding cleaned arrays and diagnostic products.
    """
    logger = log or logging.getLogger(__name__)
    logger.debug("Iterative cleaning of RFI")

    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    if x_arr.ndim != 1 or y_arr.ndim != 1:
        # raise ValueError("x and y must be 1D arrays")
        return CleanedScan(
            x=x,
            y=y,
            rms=None,
            residual=None,
            spline_max=None,
            spline=None,
            points_deleted=None,
            flag=32,
            raw_rms=None,
            raw_residuals=None,
            message = "x and y must be 1D arrays"
        )

    if x_arr.size != y_arr.size:
        # raise ValueError("x and y must have the same length")
        return CleanedScan(
            x=x,
            y=y,
            rms=None,
            residual=None,
            spline_max=None,
            spline=None,
            points_deleted=None,
            flag=31,
            raw_rms=None,
            raw_residuals=None,
            message = "x and y must have the same length"
        )

    if x_arr.size < 10:
        # raise ValueError("scan is too short for cleaning")
        return CleanedScan(
            x=x,
            y=y,
            rms=None,
            residual=None,
            spline_max=None,
            spline=None,
            points_deleted=None,
            flag=30,
            raw_rms=None,
            raw_residuals=None,
            message = "scan is too short for cleaning"
        )

    # Initial spline and residuals on raw data
    raw_spline = spline_fit_1d(y_arr,log=log)
    raw_fit = calc_residual(raw_spline, y_arr, logger)

    # Iterative cleaning
    cleaning = clean_data_iterative_fitting(
            x=x_arr,
            y=y_arr,
            res=raw_fit.residuals,
            rms=raw_fit.rms,
            log=logger,
        )
    
    return CleanedScan(
        x=cleaning.x,
        y=cleaning.y,
        rms=cleaning.rms,
        residual=cleaning.residual,
        spline_max=cleaning.spline_max,
        spline=cleaning.spline,
        points_deleted=cleaning.points_deleted,
        flag=cleaning.flag,
        raw_rms=float(raw_fit.rms),
        raw_residuals=np.asarray(raw_fit.residuals, dtype=float),
        message = "Ok"
    )


def clean_data_iterative_fitting(
    x: Union[np.ndarray, Sequence[float]],
    y: Union[np.ndarray, Sequence[float]],
    res: Union[np.ndarray, Sequence[float]],
    rms: float,
    log: logging.Logger,
    x2: Optional[Sequence[Any]] = None,
    cut: float = 3.0,
    max_iters: int = 25,
) -> IterativeCleaningResult:
    """
    Iteratively remove RFI-like outliers and refit a spline until RMS no longer 
    improves.

    A point is kept if |residual| <= cut * rms.

    Parameters
    ----------
    x, y
        1D arrays of equal length.
    res
        1D residual array aligned with x and y (for the current iteration).
    rms
        Current RMS estimate used for thresholding.
    log
        Logger instance.
    x2
        Optional aligned metadata (filenames, IDs). If provided, it is filtered too.
    cut
        Residual threshold multiplier.
    max_iters
        Safety cap on number of iterations.

    Returns
    -------
    Without x2:
        finalX, finalY, finalRms, finalRes, finalMaxSpl, finalSplinedData, pointsDeleted
    With x2:
        finalX, finalY, finalRms, finalRes, finalMaxSpl, finalSplinedData, pointsDeleted, finalNames
    """
    log.debug("Performing iterative RFI cuts on data")

    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    res_arr = np.asarray(res, dtype=float)

    if x_arr.ndim != 1 or y_arr.ndim != 1 or res_arr.ndim != 1:
        return IterativeCleaningResult(
            x=x_arr.ravel(),
            y=y_arr.ravel(),
            rms=np.nan,
            residual=res_arr.ravel(),
            spline_max=np.nan,
            spline=spline_fit_1d(y_arr.ravel(), log=log),
            points_deleted=0,
            flag=32,
            names=list(x2) if x2 is not None else None,
            message="x, y, and res must be 1D arrays",
        )

    n = x_arr.size
    if y_arr.size != n or res_arr.size != n:
        return IterativeCleaningResult(
            x=x_arr,
            y=y_arr,
            rms=np.nan,
            residual=res_arr,
            spline_max=np.nan,
            spline=spline_fit_1d(y_arr, log=log),
            points_deleted=0,
            flag=31,
            names=list(x2) if x2 is not None else None,
            message="x, y, and res must have the same length",
        )

    if x2 is not None:
        names_arr = np.asarray(x2, dtype=object)
        if names_arr.ndim != 1 or names_arr.size != n:
            return IterativeCleaningResult(
                x=x_arr,
                y=y_arr,
                rms=np.nan,
                residual=res_arr,
                spline_max=np.nan,
                spline=spline_fit_1d(y_arr, log=log),
                points_deleted=0,
                flag=33,
                names=list(x2),
                message="x2 must be 1D and the same length as x",
            )
    else:
        names_arr = None

    if not np.isfinite(rms) or rms <= 0.0:
        msg=f"RFI cleaning rms invalid (rms={rms}). Skipping further cleaning for this scan."
        log.warning(msg)
        spline_y = spline_fit_1d(y_arr, log=log)
        spline_max = float(np.nanmax(spline_y)) if spline_y.size else float("nan")
        return IterativeCleaningResult(
            x=x_arr,
            y=y_arr,
            rms=np.nan,
            residual=res_arr,
            spline_max=spline_max,
            spline=spline_y,
            points_deleted=0,
            flag=28,
            names=names_arr.tolist() if names_arr is not None else None,
            message=msg,
        )

    # Best state (start as original)
    best_x = x_arr
    best_y = y_arr
    best_res = res_arr
    best_rms = float(rms)
    best_names = names_arr

    best_spline = spline_fit_1d(best_y,log=log)
    best_max_spline = float(np.nanmax(best_spline))

    for it in range(1, max_iters + 1):
        threshold = cut * best_rms
        keep_mask = np.abs(best_res) <= threshold

        # If nothing changes, stop.
        kept_count = int(np.count_nonzero(keep_mask))
        if kept_count == best_y.size:
            log.debug(f"No additional points rejected at iteration {it}. Stopping.")
            break

        if kept_count < 10:
            log.debug(f"Too few points remain ({kept_count}) at iteration {it}. Stopping.")
            break

        new_x = best_x[keep_mask]
        new_y = best_y[keep_mask]
        new_names = best_names[keep_mask] if best_names is not None else None

        spline_y = spline_fit_1d(new_y,log=log)
        max_spline = float(np.nanmax(spline_y))

        residual_fit = calc_residual(spline_y, new_y, log)
        new_res = np.asarray(residual_fit.residuals, dtype=float)
        new_rms = float(residual_fit.rms)

        log.debug(
            f"Iter {it}: rejected={best_y.size - kept_count}, rms {best_rms:.6g} -> {new_rms:.6g}"
        )

        # Accept only if RMS improves.
        if np.isfinite(new_rms) and new_rms < best_rms:
            best_x = new_x
            best_y = new_y
            best_res = new_res
            best_rms = new_rms
            best_spline = spline_y
            best_max_spline = max_spline
            best_names = new_names
        else:
            break

    points_deleted = int(n - best_y.size)

    if best_names is None:
        return IterativeCleaningResult(
            x=best_x,
            y=best_y,
            rms=float(best_rms) if np.isfinite(best_rms) else float("nan"),
            residual=best_res,
            spline_max=float(best_max_spline),
            spline=best_spline,
            points_deleted=points_deleted,
            flag=29,
            names=best_names.tolist() if best_names is not None else None,
            message="No names/dates given for iterative clean",
        ) #best_x, best_y, best_rms, best_res, best_max_spline, best_spline, points_deleted

    log.debug(
        f"Iterative cleaning removed {points_deleted} points. Remaining={best_names.size}"
    )
    return IterativeCleaningResult(
        x=best_x,
        y=best_y,
        rms=float(best_rms) if np.isfinite(best_rms) else float("nan"),
        residual=best_res,
        spline_max=float(best_max_spline),
        spline=best_spline,
        points_deleted=points_deleted,
        flag=0,
        names=best_names.tolist() if best_names is not None else None,
        message="OK",
    )


def calc_residual(model: np.ndarray, 
                  data: np.ndarray,
                  log:logging.Logger) -> ResidualFit:
    """
        Calculate the residual and rms between the model and the data.

        Parameters:
            model (array): 1D array containing the model data
            data (array): 1D array containing the raw data
            log (object): file logging object

        Returns
        -------
        res: 1d array
            the residual
        rms: int
            the rms value
    """

    log.debug('Calculating residual error and rms between model and data')

    res = (model - data)
    res = np.asarray(model - data, dtype=float)
    rms = float(np.sqrt(np.nanmean(res ** 2)))

    return ResidualFit(residuals=res, 
                       rms=rms)
