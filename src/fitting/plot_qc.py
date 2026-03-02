# =========================================================================== #
# File: plot_qc.py                                                            #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
# =========================================================================== #


@dataclass(slots=True)
class ScanQualityResult:
    # Defaults represent "QC not computed yet".
    ok: bool = False
    flag: int = 0
    message: str = "QC not computed"
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "flag": getattr(self, "flag", None),
            "message": getattr(self, "message", ""),
            "ok": getattr(self, "ok", None),
            "metrics": getattr(self, "metrics", {}),
        }

def _mad(x: np.ndarray) -> float:
    """
    Compute the median absolute deviation (MAD) of a numeric array.

    MAD is defined as the median of the absolute differences between each
    value and the median of the data. It provides a robust measure of
    statistical dispersion and resists the influence of outliers.

    Non-finite values such as NaN and infinity are removed before
    computation. If no finite values remain, NaN is returned.

    Parameters
    ----------
    x : np.ndarray
        Input array of numeric values.

    Returns
    -------
    float
        The median absolute deviation of the input data, or NaN if the
        input contains no finite values.

    Notes
    -----
    This function returns the raw MAD value. To approximate the standard
    deviation for normally distributed data, multiply the result by
    1.4826.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    med = np.median(x)
    return float(np.median(np.abs(x - med)))

def _local_maxima_indices(y: np.ndarray) -> np.ndarray:
    """
    Return indices of local maxima in a one-dimensional numeric array.

    A local maximum is defined as a point whose value is greater than
    both its immediate neighbors. Endpoints are excluded, and flat
    plateaus are not considered maxima.

    Parameters
    ----------
    y : np.ndarray
        Input array of numeric values.

    Returns
    -------
    np.ndarray
        Array of integer indices where local maxima occur. Returns an
        empty array if fewer than three elements are provided.

    Notes
    -----
    The implementation detects sign changes in the first derivative
    from positive to negative. This method is efficient and robust for
    smooth signals but does not detect flat or multi-point peaks.
    """
    y = np.asarray(y, dtype=float)
    if y.size < 3:
        return np.array([], dtype=int)
    return (np.diff(np.sign(np.diff(y))) < 0).nonzero()[0] + 1

def check_scan_quality(
    x: np.ndarray,
    y_corrected: np.ndarray,
    y_spline: np.ndarray,
    hfnbw: float,
    hhpbw: float,
    peak_coeffs: Optional[np.ndarray],
    peak_x: Optional[np.ndarray],
    peak_y: Optional[np.ndarray],
    peak_model: Optional[np.ndarray],
    band: str,
) -> ScanQualityResult:
    
    x = np.asarray(x, dtype=float)
    y = np.asarray(y_corrected, dtype=float)
    ys = np.asarray(y_spline, dtype=float)

    metrics: Dict[str, Any] = {}

    if x.size < 20 or y.size != x.size:
        return ScanQualityResult(False, 34, "invalid input length", metrics)

    max_spline = np.nanmax(ys)
    peak_height = float(max_spline) if np.isfinite(max_spline) else float("nan")
    metrics["peak_height"] = peak_height

    # pmin=min(peak_y)
    # pmax=max(peak_y)
    # print(pmin,pmax, pmax-pmin)
    
    if not np.isfinite(peak_height) or peak_height <= 0:
        return ScanQualityResult(False, 35, "non-finite or non-positive peak height", metrics)

    # 1) Step detection
    dy = np.diff(y)
    mad_dy = _mad(dy)
    metrics["mad_dy"] = mad_dy

    if np.isfinite(mad_dy) and mad_dy > 0:
        step_k = 8.0
        step_hits = int(np.count_nonzero(np.abs(dy) > step_k * mad_dy))
        step_frac = step_hits / max(1, dy.size)
        metrics["step_hits"] = step_hits
        metrics["step_frac"] = step_frac
        if step_frac > 0.01:
            return ScanQualityResult(False, 36, "step-like jumps detected", metrics)

    # Regions
    main_mask = np.abs(x) <= hfnbw
    wing_mask = np.abs(x) >= hfnbw

    # 2) Multi-peak test inside FNBW
    main_max_idx = _local_maxima_indices(ys[main_mask])
    if main_max_idx.size > 0:
        main_vals = ys[main_mask][main_max_idx]
        strong = main_vals >= 0.60 * float(np.nanmax(ys[main_mask]))
        strong_count = int(np.count_nonzero(strong))
        metrics["main_local_max_count"] = int(main_max_idx.size)
        metrics["main_strong_max_count"] = strong_count
        if strong_count > 1:
            return ScanQualityResult(False, 37, "multiple strong peaks in main beam", metrics)

    # 3) Baseline flatness outside FNBW
    if int(np.count_nonzero(wing_mask)) >= 10:
        wing_y = y[wing_mask]
        wing_x = x[wing_mask]
        wing_mean = abs(float(np.nanmean(wing_y)))
        wing_std = float(np.nanstd(wing_y))
        metrics["wing_mean"] = wing_mean
        metrics["wing_std"] = wing_std

        mean_lim = 0.2 * peak_height #0.05
        std_lim = 0.2 * peak_height #0.10
        if wing_std > 1.5*std_lim:
            return ScanQualityResult(False, 44, f"baseline too noisy or structured (>1.5*std), wing std: {wing_std:.2f}, peak std lim: {std_lim:.2f}", metrics)
        if wing_mean > mean_lim:
            return ScanQualityResult(False, 38, f"baseline mean too far from zero, wing mean: {wing_mean:.2f}, peak mean lim: {mean_lim:.2f} ", metrics)
        # if wing_std > std_lim:
        #     return ScanQualityResult(False, 39, f"baseline too noisy or structured, wing std: {wing_std:.2f}, peak std lim: {std_lim:.2f}", metrics)

        # slope in wings
        try:
            coeff = np.polyfit(wing_x[np.isfinite(wing_y)], wing_y[np.isfinite(wing_y)], 1)
            wing_slope = float(coeff[0])
        except Exception:
            wing_slope = float("nan")
        metrics["wing_slope"] = wing_slope

        slope_lim = (0.20 * peak_height) / max(hfnbw, 1e-6)
        if np.isfinite(wing_slope) and abs(wing_slope) > slope_lim:
            return ScanQualityResult(False, 40, "baseline slope too large", metrics)

    # 4) Peak concavity and vertex position
    if peak_coeffs is not None and len(peak_coeffs) >= 3:
        a = float(peak_coeffs[0])
        b = float(peak_coeffs[1])
        metrics["peak_coeff_a"] = a
        metrics["peak_coeff_b"] = b

        if not np.isfinite(a) or a >= 0.0:
            return ScanQualityResult(False, 41, "peak parabola not concave down", metrics)

        x0 = -b / (2.0 * a)
        metrics["peak_vertex_x"] = x0

        if peak_x is not None and peak_x.size > 0:
            xmin = float(np.nanmin(peak_x))
            xmax = float(np.nanmax(peak_x))
            metrics["peak_fit_xmin"] = xmin
            metrics["peak_fit_xmax"] = xmax
            if not (xmin <= x0 <= xmax):
                return ScanQualityResult(False, 42, "peak vertex outside fit window", metrics)

    # 6) Peak residual quality
    if peak_y is not None and peak_model is not None and peak_y.size == peak_model.size and peak_y.size >= 10:
        resid = peak_y - peak_model
        peak_rms = float(np.sqrt(np.nanmean(resid**2)))
        rel = peak_rms / peak_height
        metrics["peak_rms"] = peak_rms
        metrics["peak_rel_rms"] = rel
        if np.isfinite(rel) and rel > 0.2: #0.08:
            # print(peak_rms)
            return ScanQualityResult(False, 43, f"peak fit residual too large, peak_rms: {peak_rms:.2f}, peak_rel_rms: {rel:.2f}  ", metrics)

    
    # 7) Negative tail check
    # tail_min = float(np.nanmin(y[wing_mask])) if int(np.count_nonzero(wing_mask)) else float("nan")
    # metrics["tail_min"] = tail_min
    # if np.isfinite(tail_min) and tail_min < (-0.20 * peak_height):
    #     return ScanQualityResult(False, 44, "negative tail too deep", metrics)

    return ScanQualityResult(True, 0, "OK", metrics)
