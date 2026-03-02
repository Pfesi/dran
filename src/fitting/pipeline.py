# =========================================================================== #
# File: pipeline.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import sys
from typing import Optional,Any
import numpy as np
from src.config.paths import ProjectPaths
from src.fitting.baseline_correction import correct_baseline_linear
from src.fitting.baseline_windows import build_baseline_windows, filter_invalid_minima
from src.fitting.gaussian_fit import fit_gaussian_test
from src.fitting.models import BeamFitResult, DualBeamFitResult, ScanQualityResult, DualBeamQCResult
from src.fitting.plotting import plot_diagnostics, plot_fail
from src.fitting.peak_fitting import fit_quadratic_peak, calc_residual, peak_location_index, peak_window_indices
from src.fitting.rfi_cleaning import  clean_data
from src.fitting.validation import validate_xy
from src.fitting.plot_qc import check_scan_quality
from dataclasses import dataclass
# =========================================================================== #

    
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


def find_step_locations(y: np.ndarray, sigma: float, sigma_mult: float
                        ) -> np.ndarray:
    """Identify step change locations in a signal.
    Finds indices where the absolute first difference exceeds a multiple 
    of the noise level.
    """

    if y.size < 3 or sigma <= 0.0:
        return np.array([], dtype=int)
    dy = np.diff(y)
    idx = np.where(np.abs(dy) > (sigma_mult * sigma))[0]
    return idx


def plot_dual_beam_final(
    *,
    x: np.ndarray,
    y: np.ndarray,
    y_corr: np.ndarray,
    a_idx: np.ndarray,
    b_idx: np.ndarray,
    a_model_x: np.ndarray,
    a_model_y: np.ndarray,
    b_model_x: np.ndarray,
    b_model_y: np.ndarray,
    a_label: str,
    b_label: str,
    qc_flag: int,
    qc_reasons: list[str],
    base_sigma: float,
    save: str,
    paths: Any,
    log: Any,
) -> None:
    """Generate and save the final dual-beam diagnostic plot.
    Detects step edges in the corrected scan, builds plotting series for 
    the corrected data, beam windows, fitted beam models, and optional step 
    markers, then calls plot_diagnostics to render the final QC plot.
    """

    sigma = base_sigma if base_sigma > 0 else float(np.std(y_corr))
    step_idx = find_step_locations(y_corr, sigma, 12.0)

    lines = []
    lines.append(f"flag={qc_flag}")
    if base_sigma > 0:
        lines.append(f"base_rms={base_sigma:.4g}")
    if step_idx.size:
        lines.append(f"step_edges={step_idx.size}")

    if qc_reasons:
        lines.extend(qc_reasons[:6])

    qc_text = "\n".join(lines)

    series = [
        {"x": x, "y": y_corr, "lab": "corrected", "fmt": "k"},
        {"x": x[a_idx], "y": y_corr[a_idx], "lab": "beam A window", "fmt": ""},
        {"x": x[b_idx], "y": y_corr[b_idx], "lab": "beam B window", "fmt": ""},
        {"x": a_model_x, "y": a_model_y, "lab": a_label, "fmt": ""},
        {"x": b_model_x, "y": b_model_y, "lab": b_label, "fmt": ""},
    ]

    # Add step markers if present
    if step_idx.size:
        step_x = x[step_idx]
        step_y = y_corr[step_idx]
        series.append({"x": step_x, "y": step_y, "lab": "step", "fmt": "x"})

    plot_diagnostics(
        series,
        paths,
        log,
        save,
        plot_type="final",
        suffix="_dual_beam_final.png",
        # annotation=qc_text,
        # annotation_loc="upper left",
    )


def robust_sigma(y: np.ndarray) -> float:
    """Estimate robust noise level using the median absolute deviation.
    Falls back to standard deviation for small samples and returns zero for 
    empty input.
    """

    if y.size < 5:
        return float(np.std(y)) if y.size else 0.0
    med = float(np.median(y))
    mad = float(np.median(np.abs(y - med)))
    return 1.4826 * mad


def step_metrics(y: np.ndarray, sigma: float, sigma_mult: float
                 ) -> tuple[float, int]:
    """Compute step change metrics for a signal.
    Returns the maximum absolute step size and the count of steps exceeding 
    a noise-scaled threshold.
    """

    if y.size < 3:
        return 0.0, 0

    dy = np.diff(y)
    if sigma <= 0.0:
        return float(np.max(np.abs(dy))) if dy.size else 0.0, 0

    threshold = sigma_mult * sigma
    step_count = int(np.sum(np.abs(dy) > threshold))
    step_max = float(np.max(np.abs(dy))) if dy.size else 0.0
    return step_max, step_count


def max_gap_fraction(x: np.ndarray) -> float:
    """Compute the largest sampling gap relative to the median spacing.
    Returns the ratio of the maximum gap to the median step size, or zero 
    for insufficient or degenerate input.
    """
    
    if x.size < 3:
        return 0.0
    dx = np.diff(np.sort(x))
    med = float(np.median(dx)) if dx.size else 0.0
    if med <= 0.0:
        return 0.0
    max_gap = float(np.max(dx))
    return max_gap / med


def edge_distance_fraction(
    peak_x: float,
    window_left: float,
    window_right: float,
) -> float:
    """Measure normalized distance of a peak from the window edges.
    Returns the minimum distance to either edge divided by the window 
    width, with a fallback value for invalid windows.
    """

    width = window_right - window_left
    if width <= 0:
        return 1.0
    d_left = abs(peak_x - window_left)
    d_right = abs(window_right - peak_x)
    d_edge = min(d_left, d_right)
    return d_edge / width


def compute_dual_beam_qc(
    x: np.ndarray,
    y_corrected: np.ndarray,
    baseline_sigma: float,
    a_idx: np.ndarray,
    b_idx: np.ndarray,
    a_peak: float,
    a_peak_x: float,
    a_resid: np.ndarray,
    b_peak: float,
    b_peak_x: float,
    b_resid: np.ndarray,
    a_window: tuple[float, float],
    b_window: tuple[float, float],
    cfg: DualBeamQCConfig,
) -> DualBeamQCResult:
    
    """Evaluate dual-beam scan quality and return QC diagnostics.
    Computes robust noise, step discontinuities, sampling gaps, per-beam 
    point counts, residual RMS, SNR, amplitude balance, edge proximity, 
    and peak sign consistency. Produces a QC flag and reason list, plus 
    summary metrics used for logging and plotting.
    """
    reasons: list[str] = []

    noise_sigma = robust_sigma(y_corrected) if baseline_sigma <= 0 else baseline_sigma
    step_max, step_count = step_metrics(y_corrected, noise_sigma, cfg.step_sigma_mult)
    gap_frac = max_gap_fraction(x)

    if step_max > cfg.step_sigma_mult * noise_sigma:
        reasons.append(f"large step discontinuity. step_max={step_max:.4g}, sigma={noise_sigma:.4g}")

    if step_count > cfg.step_count_max:
        reasons.append(f"too many step edges. step_count={step_count}")

    if gap_frac > (1.0 + cfg.max_gap_frac):
        reasons.append(f"large gap in x sampling. gap_frac={gap_frac:.3f}")

    if a_idx.size < cfg.min_points_per_beam:
        reasons.append(f"too few points in A beam. n={a_idx.size}")

    if b_idx.size < cfg.min_points_per_beam:
        reasons.append(f"too few points in B beam. n={b_idx.size}")

    resid_rms_a = float(np.sqrt(np.mean(a_resid * a_resid))) if a_resid.size else float("inf")
    resid_rms_b = float(np.sqrt(np.mean(b_resid * b_resid))) if b_resid.size else float("inf")

    if baseline_sigma > 0.0:
        if resid_rms_a / baseline_sigma > cfg.max_resid_to_baseline_rms:
            reasons.append(f"A fit residual too large. resid_rms={resid_rms_a:.4g}, base_rms={baseline_sigma:.4g}")
        if resid_rms_b / baseline_sigma > cfg.max_resid_to_baseline_rms:
            reasons.append(f"B fit residual too large. resid_rms={resid_rms_b:.4g}, base_rms={baseline_sigma:.4g}")

    snr_a = abs(a_peak) / baseline_sigma if baseline_sigma > 0 else 0.0
    snr_b = abs(b_peak) / baseline_sigma if baseline_sigma > 0 else 0.0

    if snr_a < cfg.min_snr:
        reasons.append(f"low SNR on A. snr={snr_a:.2f}")
    if snr_b < cfg.min_snr:
        reasons.append(f"low SNR on B. snr={snr_b:.2f}")
        
    if abs(a_peak) < 0.5*abs(b_peak):
        reasons.append('Peak A is less than 50% peak B')
    if abs(b_peak) < 0.5*abs(a_peak):
        reasons.append('Peak B is less than 50% peak A')

    amp_ratio = (abs(a_peak) / max(abs(b_peak), 1e-12)) if b_peak != 0 else float("inf")
    if amp_ratio > cfg.max_amp_ratio or amp_ratio < (1.0 / cfg.max_amp_ratio):
        reasons.append(f"amplitude imbalance. ratio={amp_ratio:.2f}")

    # a_edge = edge_distance_fraction(a_peak_x, a_window[0], a_window[1])
    # b_edge = edge_distance_fraction(b_peak_x, b_window[0], b_window[1])
    # if a_edge < cfg.max_edge_frac:
    #     reasons.append("A peak too close to window edge")
    # if b_edge < cfg.max_edge_frac:
    #     reasons.append("B peak too close to window edge")

    # Opposite-sign requirement for dual beam
    if np.sign(a_peak) == np.sign(b_peak):
        reasons.append("A and B peaks have same sign")

    is_bad = len(reasons) > 0

    # Flag mapping. Keep your existing numeric scheme, but make it consistent.
    # 0 ok
    # 60 QC bad scan
    # 61 strong step
    flag = 0
    if is_bad:
        flag = 60
        if any("step discontinuity" in r for r in reasons):
            flag = 61

    return DualBeamQCResult(
        is_bad=is_bad,
        flag=flag,
        reasons=reasons,
        step_max=step_max,
        step_count=step_count,
        max_gap_frac=gap_frac,
        snr_a=float(snr_a),
        snr_b=float(snr_b),
        resid_rms_a=resid_rms_a,
        resid_rms_b=resid_rms_b,
    )

def dual_beam_qc_to_scan_quality(qc: DualBeamQCResult) -> ScanQualityResult:
    metrics = {
        "step_max": qc.step_max,
        "step_count": qc.step_count,
        "max_gap_frac": qc.max_gap_frac,
        "snr_a": qc.snr_a,
        "snr_b": qc.snr_b,
        "resid_rms_a": qc.resid_rms_a,
        "resid_rms_b": qc.resid_rms_b,
        "reasons": list(qc.reasons),
    }
    return ScanQualityResult(
        ok=not qc.is_bad,
        flag=qc.flag,
        message="OK" if not qc.is_bad else " | ".join(qc.reasons),
        metrics=metrics,
    )
    
    
def fit_scan(
    x: np.ndarray,
    y: np.ndarray,
    band: str,
    hfnbw: float,
    hhpbw: float,
    force: bool,
    log: logging.Logger,
    save: str,
    theofit: str,
    autofit: str,
    paths:ProjectPaths,
) -> BeamFitResult:
    """
    Refactored pipeline wrapper around the existing logic.
    Long, scan-specific heuristics stay in this file, while reusable parts live in modules.

    This version removes sys.exit calls. It returns BeamFitResult with flag and message.
    """
    result = BeamFitResult()
    # print('validate: ',x,y)
    try:
        validate_xy(x, y, log)
    except ValueError as exc:
        flag=1
        msg='Failed to validate data'
        result.flag = flag
        result.message = str(exc)
        if len(x)!=len(y):
            if len(x)>len(y):
                y = np.full_like(x, y)
            else:
                x = np.full_like(y, x)
            plot_fail(x,y , paths, msg, log, save, flag, fmt="red")
        else:
            plot_fail(x, y, paths, msg, log, save, flag, fmt="red")
        return result

    plot_diagnostics([{"x": x, "y": y, "lab": "raw", "fmt": ""}], 
                     paths,
                     log, 
                     save, 
                     suffix="_raw.png")

    # Quick Gaussian gate
    p0 = [float(np.max(y)), float(np.mean(x)), float(hhpbw * 2.0), 0.01, 0.0]
    _, _, gauss_flag = fit_gaussian_test(x, y, p0, log)
    if gauss_flag is not None:
        result.flag = 8
        result.message = "Gaussian test fit failed"
        plot_fail(x, y,paths, result.message, log, save, flag=result.flag, fmt="orange")
        return result

    # RFI cleaning
    clean = clean_data(x, y, log)
    result.clean_rms = clean.rms

    # Derivative step masking (kept from your flow, packaged here)
    dy = np.diff(clean.y)
    std = float(np.std(dy)) if dy.size else 0.0
    threshold = 2.0 * std
    step_idx = np.where(np.abs(dy) >= threshold)[0]
    mask = np.zeros(len(dy), dtype=bool)
    mask[step_idx] = True

    clean2 = clean_data(clean.x[:-1][~mask], clean.y[:-1][~mask], log)
    plot_diagnostics(
        [
            {"x": clean.x, "y": clean.y, "lab": "cleaned", "fmt": ""},
            {"x": clean2.x, "y": clean2.y, "lab": "cleaned_new", "fmt": ""},
        ],
        paths,
        log,
        save,
        suffix="_cleaned_new.png",
    )

    clean = clean2
    
    # # Quick Gaussian gate after clean
    # p0 = [float(np.max(clean.y)), float(np.mean(clean.x)), float(hhpbw * 2.0), 0.01, 0.0]
    # _, _, gauss_flag = fit_gaussian_test(clean.x, clean.y, p0, log)
    # if gauss_flag is not None:
    #     plot_fail(clean.x, clean.y,paths, "Gaussian test fit failed", log, save, flag=5, fmt="orange")
    #     result.flag = 5
    #     result.message = "Gaussian test fit failed"
    #     return result
    

    # Baseline point discovery via spline extrema
    if clean.spline is None:
        msg= "Failed to spline data"
        result.message =msg
        result.flag = 11
        plot_fail(x, y, paths,msg, log, save, flag=result.flag, fmt="tomato")
        
        return result
        # print(result)
        # sys.exit()
    else:
        local_min = (np.diff(np.sign(np.diff(clean.spline))) > 0).nonzero()[0] + 1
        local_max = (np.diff(np.sign(np.diff(clean.spline))) < 0).nonzero()[0] + 1

    max_points = 50
    local_min = filter_invalid_minima(local_max, local_min, max_points=max_points, log=log)

    if local_min.size == 0 and local_max.size == 0:
        result.flag = 12
        result.message = "Failed to locate minima and maxima"
        plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="coral")
        return result

    # Spline peak and beam markers
    spline_peak_idx = int(np.argmax(clean.spline))
    x_spline_peak = float(clean.x[spline_peak_idx])

    xhpbw_left = x_spline_peak - hhpbw
    xhpbw_right = x_spline_peak + hhpbw
    xfnbw_left = x_spline_peak - hfnbw
    xfnbw_right = x_spline_peak + hfnbw

    if not (-hfnbw <= x_spline_peak <= hfnbw):
        result.flag = 13
        result.message = "Peak not within expected half-first-null width"
        plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="m")
        return result

    # print(clean.x, xhpbw_left, xhpbw_right,xfnbw_left )

    left_hpbw_idx = int(np.where(clean.x >= xhpbw_left)[0][0])

    try:
        right_hpbw_idx = int(np.where(clean.x >= xhpbw_right)[0][0])
    except:
        log.debug('Right hpbw couldnt be estimated')
        result.flag = 14
        result.message = "Right hpbw estimation failed"
        plot_fail(x, y, paths,"Right hpbw estimation failed", log, save, flag=result.flag, fmt="m")
        
        return result

    left_fnbw_idx = int(np.where(clean.x >= xfnbw_left)[0][0])

    right_fnbw_idx: Optional[int]
    rr = np.where(clean.x >= xfnbw_right)[0]
    right_fnbw_idx = int(rr[0]) if rr.size else None

    # Split minima by side
    left_mins = [int(v) for v in local_min if clean.x[int(v)] < xhpbw_left]
    right_mins = [int(v) for v in local_min if clean.x[int(v)] > xhpbw_right]

    baseline_indices, base_flag = build_baseline_windows(
        x=clean.x,
        left_mins=left_mins,
        right_mins=right_mins,
        left_hpbw_idx=left_hpbw_idx,
        right_hpbw_idx=right_hpbw_idx,
        left_fnbw_idx=left_fnbw_idx,
        right_fnbw_idx=right_fnbw_idx,
        max_points=max_points,
        log=log,
    )

    y_corrected, y_corr_spline, base_coeffs, base_res, base_rms = correct_baseline_linear(
        x=clean.x,
        y=clean.y,
        baseline_indices=baseline_indices,
        log=log,
    )

    result.baseline_coeffs = base_coeffs
    result.baseline_residual = base_res
    result.baseline_rms = float(base_rms)
    result.baseline_window_indices = baseline_indices
    result.y_corrected = y_corrected
    result.y_corrected_spline = y_corr_spline

    plot_diagnostics(
        [
            {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": ""},
            {"x": clean.x[baseline_indices], "y": y_corrected[baseline_indices], "lab": "base locs", "fmt": "."},
            {"x": clean.x, "y": y_corr_spline, "lab": "splined", "fmt": ""},
        ],
        paths,
        log,
        save,
        suffix="_corrected.png",
    )

    # Peak selection and quadratic fit
    # max_spline = float(np.max(y_corr_spline))
    # spline_peak2_idx = int(np.argmax(y_corr_spline))
    # x_spline_peak2 = float(clean.x[spline_peak2_idx])

    # Cut fraction heuristic preserved
    cut_fraction = 0.7
    fx_idx = peak_window_indices(clean.x, y_corr_spline, hfnbw=hfnbw, cut_fraction=cut_fraction)

    if fx_idx.size == 0:
        result.flag = 24
        result.message = "No peak points selected"
        plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="darkorange")
        
        return result

    px = clean.x[fx_idx]
    py = y_corrected[fx_idx]

    peak_coeffs, peak_model, peak_rms = fit_quadratic_peak(px, py, log)
    # print('coeffs: ', peak_coeffs)
    
    if len(peak_coeffs)==0:
        result.flag = 60
        result.message = "Peak coeffs = 0, failed peak fit"
        plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="r")
        
        return result
    
    is_concave_down = np.isfinite(peak_coeffs[0]) and (peak_coeffs[0] < 0.0)
    if not is_concave_down:
        result.flag = 25
        result.message = "Failed to fit peak accurately"
        plot_fail(x, y, paths,result.message, log, save, flag=5, fmt="sienna")
        return result

    peak_loc = peak_location_index(peak_model)
    ta_peak = float(np.max(peak_model)) if peak_model.size else float("nan")
    rel_error = (peak_rms / ta_peak) * 100.0 if ta_peak and np.isfinite(ta_peak) else float("inf")

    if not np.isfinite(rel_error) or rel_error >= 100.0:
        result.flag = 23
        result.message = "Peak fit relative error too high"
        plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="r")
        
        return result

    result.peak_coeffs = peak_coeffs
    result.peak_model = peak_model
    result.ta_peak = ta_peak
    result.ta_peak_err = float(peak_rms)
    result.peak_loc_index = int(peak_loc)
    result.flag = 0
    result.message = "OK"

    # apply qc check only if you want strict outlier detection
    qc=check_scan_quality(
        x=clean.x,
        y_corrected=y_corrected,
        y_spline=y_corr_spline,
        hfnbw=hfnbw,
        hhpbw=hhpbw,
        peak_coeffs=peak_coeffs,
        peak_x=px,
        peak_y=py,
        peak_model=peak_model,
        band=band
        )
    result.qc=qc

    log.info(f"T$_A$ [K]: {ta_peak:.3f} +- {peak_rms:.3f}")    
    if qc.ok==False:
        log.warning("QC failed: %s", qc.message)
        result.flag = qc.flag
        result.message = qc.message
        if qc.flag==34: 
            c = "darkmagenta"
        elif qc.flag==35: 
            c = "darkorange"
        # elif qc.flag==102: 
        #     c = "indigo" 
        # elif qc.flag==103: 
        #     c = "indigo" 
        elif qc.flag==36: 
            c = "darkblue"
        elif qc.flag==37: 
            c = "darkgreen"   
        elif qc.flag==38: 
            c = "crimson"
        elif qc.flag==39: 
            c = "navy" 
        elif qc.flag==40: 
            c = "r"
        elif qc.flag==41: 
            c = "steelblue"    
        elif qc.flag==42: 
            c = "salmon" 
        elif qc.flag==43: 
            c = "violet"
        elif qc.flag==44: 
            c = "darkolivegreen"  
        # elif qc.flag==211: 
        #     c = "y"
        # elif qc.flag==212: 
        #     c = "grey"  
        # elif qc.flag==213: 
        #     c = "grey" 
        
        plot_fail(clean.x,y_corrected, paths,qc.message, log, save, flag=5, fmt=c)
        result.qc = qc
        
        return result

    plot_diagnostics(
        [
            {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
            {"x": px, "y": py, "lab": "peak", "fmt": ""},
            {"x": px, "y": peak_model, "lab": f"T$_A$ [K]: {ta_peak:.3f} +- {peak_rms:.3f}", "fmt": ""},
        ],
        paths,
        log,
        save,
        suffix="_corrected_final.png",
    )
    plot_diagnostics(
        [
            {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
            {"x": px, "y": py, "lab": "peak", "fmt": ""},
            {"x": px, "y": peak_model, "lab": f"T$_A$ [K]: {ta_peak:.3f} +- {peak_rms:.3f}", "fmt": ""},
        ],
        paths,
        log,
        save,
        plot_type="final",
        suffix="_corrected_final.png",
    )

    return result


def fit_scan_db(
    x: np.ndarray,
    y: np.ndarray,
    band: str,
    hfnbw: float,
    hhpbw: float,
    force: bool,
    log: logging.Logger,
    save: str,
    theofit: str,
    autofit: str,
    factor:int,
    paths:ProjectPaths,
) -> DualBeamFitResult:
    """
    Refactored pipeline wrapper around the existing logic.
    Long, scan-specific heuristics stay in this file, while reusable parts live in modules.

    This version removes sys.exit calls. It returns DualBeamFitResult with flag and message.
    """
    result = DualBeamFitResult()
    
    cfg = DualBeamQCConfig(
        step_sigma_mult=12.0,
        step_count_max=6,
        min_points_per_beam=20,
        min_snr=2.0 ,#3.0,
        max_resid_to_baseline_rms=2.5,
    )

    # try:
    # print(len(x),len(y))
    # validate_xy(x, y, log)
    # except ValueError as exc:
    #     result.flag = 1
    #     result.message = str(exc)
    #     return result

    plot_diagnostics([{"x": x, "y": y, "lab": "raw", "fmt": ""}], 
                     paths,log, save, suffix="_raw.png")

    # RFI cleaning
    clean = clean_data(x, y, log)
    result.clean_rms = clean.rms

    from matplotlib import pyplot as plt
    # plt.plot(clean.x,clean.y)
    # plt.show()
    # sys.exit()
    # Derivative step masking (kept from your flow, packaged here)
    dy = np.diff(clean.y)
    std = float(np.std(dy)) if dy.size else 0.0
    threshold = 2.0 * std
    step_idx = np.where(np.abs(dy) >= threshold)[0]
    mask = np.zeros(len(dy), dtype=bool)
    mask[step_idx] = True

    if clean.rms > 1:
        log.warning("High rms: %s", clean.rms)
        msg=f"High rms: {clean.rms}"
        result.flag=2
        plot_fail(x, y, paths,msg, log, save, flag=result.flag, fmt="r")
        
        result.message = msg
        log.debug(msg)
        # sys.exit()
        return result

    clean2 = clean_data(clean.x[:-1][~mask], clean.y[:-1][~mask], log)
    plot_diagnostics(
        [
            {"x": clean.x, "y": clean.y, "lab": "cleaned", "fmt": ""},
            {"x": clean2.x, "y": clean2.y, "lab": "cleaned_new", "fmt": ""},
        ],
        paths,
        log,
        save,
        suffix="_cleaned_new.png",
    )

    clean = clean2
  
    # Baseline point discovery via spline extrema
    if clean.spline is None:
        msg="Missing spline"
        result.flag=3
        plot_fail(x, y, paths,msg, log, save, flag=result.flag, fmt="tomato")
        
        result.message = msg
        log.debug(msg)
        # sys.exit()
        return result
    
    scanLen = len(clean.x)
    midLeftLoc = int(scanLen/4)   # estimated location of peak on left beam
    midRightLoc = midLeftLoc * 3  # estimated location of peak on right beam
    fl = 0                        # failed left gaussian fit
    fr = 0                        # failed right gaussian fit

    # LOCATE BASELINE BLOCKS
    # we don't worry about sidelobes here so baseline
    # blocks are set to edges or fnbw points
    ptLimit = int(scanLen*0.04) # Point limit, number of allowed points per base block
    baseLocsLeft  = np.arange(0,ptLimit,1)
    baseLocsRight = np.arange(scanLen-ptLimit,scanLen,1)
    baseline_indices      = list(baseLocsLeft)+list(baseLocsRight)

    if len(baseLocsLeft) == 0 or len(baseLocsRight) == 0:
        msg = "failed to locate base locs"
        log.error(msg)
        result.flag = 4
        plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
        result.message = msg
        return result
    
    log.debug(f'BaseLocsLeft: {baseLocsLeft[0]} to {baseLocsLeft[-1]} = {len(baseLocsLeft)} pts')
    log.debug(f'BaseLocsLeft: {baseLocsRight[0]} to {baseLocsRight[-1]} = {len(baseLocsRight)} pts')

    # correct drift
    y_corrected, y_corr_spline, base_coeffs, base_res, base_rms = correct_baseline_linear(
        x=clean.x,
        y=clean.y,
        baseline_indices=baseline_indices,
        log=log,
    )

    result.baseline_coeffs = base_coeffs
    result.baseline_residuals = base_res
    result.baseline_rms = float(base_rms)
    result.baseline_window_indices = baseline_indices
    result.y_corrected = y_corrected
    result.y_corrected_spline = y_corr_spline

    plot_diagnostics(
        [
            {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": ""},
            {"x": clean.x[baseline_indices], "y": y_corrected[baseline_indices], "lab": "base locs", "fmt": "."},
            {"x": clean.x, "y": y_corr_spline, "lab": "splined", "fmt": ""},
        ],
        paths,
        log,
        save,
        suffix="_corrected.png",
    )

    # Spline the data and get global max/min
    ysplmaxloc = np.argmax(y_corr_spline)
    ysplminloc = np.argmin(y_corr_spline)
    ysplmax = y_corr_spline[ysplmaxloc]
    ysplmin = y_corr_spline[ysplminloc] 

    plot_diagnostics(
        [
            {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": ""},
            {"x": clean.x[baseline_indices], "y": y_corrected[baseline_indices], "lab": "base locs", "fmt": "."},
            {"x": clean.x, "y": y_corr_spline, "lab": "splined", "fmt": ""},
            {"x": clean.x[ysplmaxloc], "y": ysplmax, "lab": "top peak", "fmt": "*"},
            {"x": clean.x[ysplminloc], "y": ysplmin, "lab": "bottom peak", "fmt": "*"},
        ],
        paths,
        log,
        save,
        suffix="_corrected_peaks.png",
    )

    # A/B BEAM DATA PROCESSING
    factoredfnbw = (hfnbw*2)*factor  # fnbw multiplied by factor
    AbeamScan = np.where(np.logical_and(clean.x > -factoredfnbw, clean.x < 0))[0]
    BbeamScan = np.where(np.logical_and(clean.x > 0, clean.x < factoredfnbw))[0]

    if len(AbeamScan) == 0 or len(BbeamScan) == 0:
        msg="A/B beam scan data == 0, no data"
        log.error(msg)
        result.flag = 5
        result.message = msg
        plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
        
        
        return result

    log.debug("- Beam seperation:")
    log.debug("Left beam indeces: {} to {}".format(AbeamScan[0], AbeamScan[-1]))
    log.debug("Right beam indeces: {} to {}\n".format(
        BbeamScan[0], BbeamScan[-1]))

    log.debug("- Data Limits")
    log.debug("base left: {}, drift A left: {}, peak A: {}, drift A right: {}".format(baseLocsLeft[-1], AbeamScan[0], ysplminloc, AbeamScan[-1]))
    log.debug("drift B left: {}, peak B: {}, drift B right: {}, base right: {}\n".format(
        BbeamScan[0], ysplmaxloc, BbeamScan[-1], baseLocsRight[0]))
    
    # figure out orientation of beam. With some scans the beams
    # are flipped e.g, pks2326-502, A beam is positive, whereas
    # j0450-81 A beam is negative.
    # find value closest to zero and use the other value to determine
    # which side to fit positive/negative peak
    lstA=[min(y_corr_spline[AbeamScan]), max(y_corr_spline[AbeamScan])]
    minA = min(lstA,key=abs)
    fa=""
    if minA==min(y_corr_spline[AbeamScan]):
        # fit A beam positive B beam negative
        log.debug("Fitting positive")
        fa="p"
    else:
        # fit A beam negative B beam positive
        log.debug("Fitting negative")
        fa="n"
    
     # TODO: should make this an option
    # Decided to change this because the software now treats both 
    # target sources and calibrators the same way
    beamCut = 0.6 # fitting top 40%, 0.7 (30% for cals) or 0.5 (50% for targets) 

    # Ensure peak is within accepted limits
    if fa=="p":
        if ysplmaxloc > AbeamScan[-1]:# or ysplminloc > beamScan[0]:
            msg = "Max is beyond left baseline block"
            log.error(msg)
            result.flag = 6
            plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
            
            result.message = msg
            return result
    
        if ysplminloc < BbeamScan[0]:#baseLocsRight[0]:  # ysplminloc < BbeamScan[0] or
            msg="Min is beyond right baseline block"
            log.error(msg)
            result.flag = 7
            plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
            
            result.message = msg
            return result
        
        # Try to fit a gaussian to determine peak parameters
        # try:
        # Quick Gaussian gate
        # set initial parameters for data fitting
        p0 = [float(np.max(y_corrected)), float(clean.x[midLeftLoc]), float(hhpbw * 2.0), 0.01, 0.0]
        # Try to fit a gaussian to determine peak location
        # this also works as a bad scan filter
        _, _, gauss_flag = fit_gaussian_test(clean.x[AbeamScan], y_corrected[AbeamScan], p0, log)
        if gauss_flag is not None:
            result.flag = 8
            result.message = "Gaussian test fit failed"
            plot_fail(x, y, paths,result.message , log, save, flag=result.flag, fmt="orange")
            fitLeft = y[AbeamScan]
            fl=1
            # return result
    

        # set initial parameters for data fitting
        p = [float(min(y_corrected)), float(clean.x[midRightLoc]), float(hhpbw * 2.0), 0.01, 0.0]
        _, _, gauss_flag = fit_gaussian_test(clean.x[BbeamScan], y_corrected[BbeamScan], p, log)
        # coeffr, fitr, flagr = test_gauss_fit(x[AbeamScan], y[AbeamScan], p,log)
        if gauss_flag is not None:
            # fr = 1
            # fitRight = y[BbeamScan]
            result.flag = 8
            result.message =  "gaussian curve_fit algorithm failed"
            plot_fail(x, y, paths,result.message , log, save, flag=result.flag, fmt="tomato")
            # fitLeft = y[AbeamScan]
            # fl=1
            # return result
        


        # Determine peak fitting location
        BbeamLeftLimit  = clean.x[ysplminloc]-hhpbw #coeffl[1] - hhpbw  # *2*.6
        BbeamRightLimit = clean.x[ysplminloc]+hhpbw
        AbeamLeftLimit  = clean.x[ysplmaxloc]-hhpbw #coeffl[1] - hhpbw  # *2*.6
        AbeamRightLimit = clean.x[ysplmaxloc]+hhpbw

        leftlocs = np.where(np.logical_and(
            clean.x >= AbeamLeftLimit, clean.x <= AbeamRightLimit))[0]
        rightlocs = np.where(np.logical_and(
            clean.x >= BbeamLeftLimit, clean.x <= BbeamRightLimit))[0]
        
        
        # plt.plot(clean.x,y_corrected)
        # plt.plot(clean.x[leftlocs],y_corrected[leftlocs])
        # plt.plot(clean.x[rightlocs],y_corrected[rightlocs])
        # plt.show()
        # sys.exit()
            
        # select part of beam to fit
        if ysplmax < 0.1:
            flag = 9
            msg = "fit entire left beam, max yspl < 0.1"
            log.warning(msg)
            leftMainBeamLocs = leftlocs
                
        else:
            topCut = np.where(y_corr_spline[leftlocs] >= ysplmax*beamCut)[0]
            leftMainBeamLocs = leftlocs[0]+np.array(topCut)


        if ysplmin > -0.1:
            flag = 10
            msg = "fit entire right beam, min yspl > -0.1"
            log.warning(msg)
            rightMainBeamLocs = rightlocs
        else:
            # try:
            bottomCut = np.where(y_corr_spline[rightlocs] <= ysplmin*beamCut)[0]
            rightMainBeamLocs = rightlocs[0]+np.array(bottomCut)
            # except IndexError:
            #     msg="Index out of bound error, bottomCut"
            #     log.warning(msg)
            #     flag = 3
            #     result.flag = flag
            #     result.message = msg
                # plot_fail(x, y, msg, log, save, flag, fmt="tomato")
                # return result


    if fa=="n":
        if ysplmaxloc < AbeamScan[-1]:# or ysplminloc > beamScan[0]:
            msg = "Max is beyond left baseline block"
            log.error(msg)
            result.flag = 26
            plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
            
            result.message = msg
            return result
    
        if ysplminloc > BbeamScan[0]:#baseLocsRight[0]:  # ysplminloc < BbeamScan[0] or
            msg="Min is beyond right baseline block"
            log.error(msg)
            result.flag = 27
            plot_fail(x, y,paths,msg, log, save, flag=result.flag, fmt="orange")
            
            result.message = msg
            return result
        
        # Try to fit a gaussian to determine peak parameters
        # try:
        # Quick Gaussian gate
        # set initial parameters for data fitting
        p0 = [float(np.min(y_corrected)), float(clean.x[midLeftLoc]), float(hhpbw * 2.0), 0.01, 0.0]
        # Try to fit a gaussian to determine peak location
        # this also works as a bad scan filter
        _, _, gauss_flag = fit_gaussian_test(clean.x[AbeamScan], y_corrected[AbeamScan], p0, log)
        if gauss_flag is not None:
            result.flag = 8
            result.message = "Gaussian test fit failed"
            plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="orange")
            # fitLeft = y[AbeamScan]
            # fl=1
            return result
    

        # set initial parameters for data fitting
        p = [float(max(y_corrected)), float(clean.x[midRightLoc]), float(hhpbw * 2.0), 0.01, 0.0]
        _, _, gauss_flag = fit_gaussian_test(clean.x[BbeamScan], y_corrected[BbeamScan], p, log)

        # coeffr, fitr, flagr = test_gauss_fit(x[AbeamScan], y[AbeamScan], p,log)
        if gauss_flag is not None:
            # fr = 1
            msg = "gaussian curve_fit algorithm failed"
            # msg_wrapper("debug", log.debug, msg)
            # fitRight = y[BbeamScan]
            result.flag = 8
            result.message = "Gaussian test fit failed"
            # fitLeft = y[AbeamScan]
            # fl=1
            plot_fail(x, y, paths,result.message, log, save, flag=result.flag, fmt="tomato")
            return result
        
        # Determine peak fitting location
        AbeamLeftLimit  = clean.x[ysplminloc]-hhpbw #coeffl[1] - hhpbw  # *2*.6
        AbeamRightLimit = clean.x[ysplminloc]+hhpbw
        BbeamLeftLimit  = clean.x[ysplmaxloc]-hhpbw #coeffl[1] - hhpbw  # *2*.6
        BbeamRightLimit = clean.x[ysplmaxloc]+hhpbw

        leftlocs = np.where(np.logical_and(
            clean.x >= AbeamLeftLimit, clean.x <= AbeamRightLimit))[0]
        rightlocs = np.where(np.logical_and(
            clean.x >= BbeamLeftLimit, clean.x <= BbeamRightLimit))[0]
        
        # plt.plot(clean.x,y_corrected)
        # plt.plot(clean.x[leftlocs],y_corrected[leftlocs])
        # plt.plot(clean.x[rightlocs],y_corrected[rightlocs])
        # plt.show()
        # print('testing')
        # sys.exit()
            
        # select part of beam to fit
        if ysplmax < 0.1:
            flag = 9
            msg = "fit entire left beam, max yspl < 0.1"
            log.warning(msg)
            rightMainBeamLocs = rightlocs
            
                
        else:
            # try:
                topCut = np.where(y_corr_spline[rightlocs] >= ysplmax*beamCut)[0]
                rightMainBeamLocs = rightlocs[0]+np.array(topCut)
            # except IndexError:
            #     msg="Index out of bound error, topCut"
            #     log.warning(msg)
            #     flag = 3
            #     result.flag = flag
            #     result.message = msg
            #     plot_fail(x, y, paths,msg, log, save, flag, fmt="tomato")
            #     return result
            

        if ysplmin > -0.1:
            flag = 10
            msg = "fit entire right beam, min yspl > -0.1"
            log.warning(msg)
            leftMainBeamLocs = leftlocs
            
        else:
            # try:
                bottomCut = np.where(y_corr_spline[rightlocs] <= ysplmin*beamCut)[0]
                leftMainBeamLocs = leftlocs[0]+np.array(bottomCut)
            # except IndexError:
            #     msg="Index out of bound error, bottomCut"
            #     log.warning(msg)
            #     flag = 3
            #     result.flag = flag
            #     result.message = msg
            #     plot_fail(x, y, paths,msg, log, save, flag, fmt="tomato")
            #     return result
            
    if len(clean.x[leftMainBeamLocs]) == 0:
        # fr = 1
        # # msg_wrapper("debug", log.debug, msg)
        # fitRight = y[BbeamScan]
        result.flag = 21
        result.message = "Failed to find left main beam locs"
        # fitLeft = y[AbeamScan]
        # fl=1
        plot_fail(x, y, paths,result.message, log, save, result.flag, fmt="tomato")
        return result
    
    # fit left peak
    ypeakl = np.polyval(
        np.polyfit(clean.x[leftMainBeamLocs], y_corrected[leftMainBeamLocs],  2), clean.x[leftMainBeamLocs])
    fitResl, err_peakl = calc_residual(y_corrected[leftMainBeamLocs], ypeakl)

    # fit right peak
    # try:
    ypeakr = np.polyval(np.polyfit(
            clean.x[rightMainBeamLocs], y_corrected[rightMainBeamLocs],  2), clean.x[rightMainBeamLocs])
    fitResr, err_peakr = calc_residual(y_corrected[rightMainBeamLocs], ypeakr)
    # except:
    #     msg="Failed to fit right peak"
    #     log.warning(msg)
    #     flag = 3
    #     result.flag = flag
    #     result.message = msg
    #     plot_fail(x, y, paths,msg, log, save, flag, fmt="tomato")
    #     return result

    if fa=="p":
        ymin = min(ypeakr)
        ymax = max(ypeakl)
    else:
        ymin = min(ypeakl)
        ymax = max(ypeakr)

    log.debug("A/B beam peak")
    if fa=="p":
        log.debug( "left: {:.3f}, max: {:.3f}, right: {:.3f}".format(
            ypeakl[0], ymax, ypeakl[-1]))
        log.debug("left: {:.3f}, min: {:.3f}, right{:.3f}".format(
            ypeakr[0], ymin, ypeakr[-1]))

        # ypeakrdata = clean.x[rightMainBeamLocs]
        # ypeakldata = clean.x[leftMainBeamLocs]

        # check data doesn't overlap
        overlapRight = set(baseLocsRight) & set(rightMainBeamLocs)
        overlapLeft = set(baseLocsLeft) & set(leftMainBeamLocs)
        # overlapbeams = set(leftMainBeamLocs) & set(rightMainBeamLocs)

        msg=("checking for overlapping beams: ")
        log.debug(msg)
        
        if len(overlapLeft) != 0:
            msg = "beams don't overlap on left"
            log.debug(msg)

            if leftMainBeamLocs[0] > baseLocsLeft[int(
                    len(baseLocsLeft)*.8)]:
                pass
            else:
                overlap = next(iter(overlapLeft))
                shift = list(leftMainBeamLocs).index(int(overlap))
                msg = "Overlap found on A beam"
                flag = 20
                log.warning(msg)

                # move beam to the left
                f = abs(len(leftMainBeamLocs)-shift)
                leftMainBeamLocs = abs(leftMainBeamLocs+f)

                # fit left peak
                ypeakl = np.polyval(np.polyfit(
                    clean.x[leftMainBeamLocs], y_corrected[leftMainBeamLocs],  2), clean.x[leftMainBeamLocs])
                fitResl, err_peakl = calc_residual(
                    y_corrected[leftMainBeamLocs], ypeakl)

                ymax = max(ypeakl)
                msg="left: {:.3f}, max: {:.3f}, right: {:.3f}".format(
                    ypeakl[0], ymax, ypeakl[-1])
                log.debug(msg)

                if(ypeakl[0] >= ymax or ypeakl[-1] >= ymax):
                    ymax = np.nan
                    err_peakl = np.nan
                else:
                    flag = 22
                    msg = "fit entire left beam"
                    log.debug(msg)

                # msg = "failed to locate base locs"
                log.error(msg)
                plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
                result.flag = flag
                result.message = msg
                return result

        if len(overlapRight) != 0:

            overlap = next(iter(overlapRight))
            shift = list(rightMainBeamLocs).index(int(overlap))

            msg = "Overlap found on B beam"
            flag = 19
            log.warning(msg)

            # move beam to the RIGHT
            f = abs(len(rightMainBeamLocs)-shift)
            rightMainBeamLocs = abs(rightMainBeamLocs-f)

            msg="beam shifted to left by {} points".format(f)
            log.debug(msg)

            # fit right peak
            ypeakr = np.polyval(np.polyfit(
                clean.x[rightMainBeamLocs], y_corrected[rightMainBeamLocs],  2), clean.x[rightMainBeamLocs])
            fitResr, err_peakr = calc_residual(
                y_corrected[rightMainBeamLocs], ypeakr)

            ymin = min(ypeakr)

            msg="left: {:.3f}, min: {:.3f}, right{:.3f}".format(
                ypeakr[0], ymin, ypeakr[-1])
            log.debug(msg)

            if(ypeakr[0] <= ymin or ypeakr[-1] <= ymin):
                ymin = np.nan
                err_peakr = np.nan

            else:
                flag = 18
                msg = "fit entire right beam"
                log.debug(msg)

            # ypeakrdata = clean.x[rightMainBeamLocs]

            # msg = "failed to locate base locs"
            log.error(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result

        if ((x[leftMainBeamLocs])[-1] > 0):
            flag = 17
            msg = "left beam data goes beyond midpoint"
            # msg = "failed to locate base locs"
            log.warning(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result
            # msg_wrapper("warning", log.warning, msg)


        if ((x[rightMainBeamLocs])[-1] < 0):
            flag = 16 
            msg = "right beam data goes beyond midpoint"
            # msg_wrapper("warning", log.warning, msg)
            # msg = "failed to locate base locs"
            log.error(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result


        
        log.info("\n")
        log.info("-"*30)
        log.info("Fit the peaks")
        log.info("-"*30)

        msg="\npeak left: {:.3f} +- {:.3f} K\npeak right: {:.3f} +- {:.3f} K\n".format(
            ymax, err_peakl, ymin, err_peakr)
        log.info(msg)

        # plt.plot(clean.x,y_corrected)
        # plt.plot(clean.x[leftlocs],y_corrected[leftlocs])
        # plt.plot(clean.x[rightMainBeamLocs],y_corrected[rightMainBeamLocs])
        # plt.show()
        # sys.exit()
        
        # find final peak loc
        ploca = np.where(ypeakl == ymax)[0]
        if len(ploca)==0:
            peakLoca=np.nan
        else:
            peakLoca = (clean.x[leftMainBeamLocs])[ploca[0]]

        # find final peak loc
        plocb = np.where(ypeakr == ymin)[0] 
        if len(plocb)==0:    
            peakLocb=np.nan
        else:
            peakLocb = (clean.x[rightMainBeamLocs])[plocb[0]]


        log.info('fit passed')
        # flag=0
        # plot_fail(x, y,paths,msg, log, save, flag=30, fmt="orange")
        # result.apeak_coeffs =
        result.apeak_residuals = fitResl
        result.ata_peak = ymax
        result.ata_peak_err = err_peakl
        result.apeak_loc_index = peakLoca

        # result.bpeak_coeffs =
        result.bpeak_residuals = fitResr
        result.bta_peak = ymin
        result.bta_peak_err = err_peakr
        result.bpeak_loc_index = peakLocb

        result.baseline_coeffs = base_coeffs
        result.baseline_residuals = base_res
        result.baseline_rms = float(base_rms)
        result.baseline_window_indices = baseline_indices
        result.y_corrected = y_corrected
        result.y_corrected_spline = y_corr_spline

        result.clean_rms = clean.rms

        # result.flag = flag
        result.message = msg


        a_idx = AbeamScan #np.where((x > -factored_fnbw) & (x < 0.0))[0]
        b_idx = BbeamScan #np.where((x > 0.0) & (x < factored_fnbw))[0]

        a_window = (float(x[a_idx[0]]), float(x[a_idx[-1]]))
        b_window = (float(x[b_idx[0]]), float(x[b_idx[-1]]))
        
        qc = compute_dual_beam_qc(
            x=x,
            y_corrected=y_corrected,
            baseline_sigma=float(base_rms),
            a_idx=a_idx,
            b_idx=b_idx,
            a_peak=float(result.ata_peak),
            a_peak_x=float(result.apeak_loc_index),
            a_resid=np.asarray(result.apeak_residuals) if result.apeak_residuals is not None else np.array([]),
            b_peak=float(result.bta_peak),
            b_peak_x=float(result.bpeak_loc_index),
            b_resid=np.asarray(result.bpeak_residuals) if result.bpeak_residuals is not None else np.array([]),
            a_window=a_window,
            b_window=b_window,
            cfg=cfg,
        )
        scan_qc = dual_beam_qc_to_scan_quality(qc)
        result.qc=scan_qc
        
        # print(qc)#;sys.exit()
        if qc.is_bad:
            result.flag = qc.flag
            result.message = "bad scan. " + " | ".join(qc.reasons)

            if qc.flag==60: 
                c = "fuchsia"
            elif qc.flag==61: 
                c = "r"
            
            log.error(msg)
            plot_fail(x, y,paths,result.message , log, save, flag=qc.flag, fmt=c)
            # result.flag = qc.flag
            # result.message = msg
            
            return result

        else:
            result.flag = 0
            result.message = "ok"

        # # print(save);sys.exit()
        # plot_dual_beam_final(
        #     x=x,
        #     y=y,
        #     y_corr=y_corrected,
        #     a_idx=a_idx,
        #     b_idx=b_idx,
        #     a_model_x=x[leftMainBeamLocs],
        #     a_model_y=ypeakl,
        #     b_model_x=x[rightMainBeamLocs],
        #     b_model_y=ypeakr,
        #     a_label=f"A T_A [K]: {result.ata_peak:.3f} +- {result.ata_peak_err:.3f}",
        #     b_label=f"B T_A [K]: {result.bta_peak:.3f} +- {result.bta_peak_err:.3f}",
        #     qc_flag=result.flag,
        #     qc_reasons=qc.reasons,
        #     base_sigma=float(base_rms),
        #     save=save,
        #     paths=paths,
        #     log=log,
        # )
        # sys.exit()
            plot_diagnostics(
                [
                    {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
                    {"x": clean.x[leftMainBeamLocs], "y": y_corrected[leftMainBeamLocs], "lab": "peak left", "fmt": ""},
                    {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": "peak left", "fmt": ""},
                    {"x": clean.x[rightMainBeamLocs], "y": y_corrected[rightMainBeamLocs], "lab": "peak right", "fmt": ""},
                    {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": "peak right", "fmt": ""},
                    {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": f"T$_A$ [K]: {ymax:.3f} +- {err_peakl:.3f}", "fmt": ""},
                    {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": f"T$_A$ [K]: {ymin:.3f} +- {err_peakr:.3f}", "fmt": ""},
                #     "\npeak left: {:.3f} +- {:.3f} K\npeak right: {:.3f} +- {:.3f} K\n".format(
                # ymax, err_peakl, ymin, err_peakr)
                ],
                paths,
                log,
                save,
                suffix="_corrected_final.png",
            )
            plot_diagnostics(
                [
                    {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
                    # {"x": clean.x[leftMainBeamLocs], "y": y_corrected[leftMainBeamLocs], "lab": "", "fmt": ""},
                    {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": "peak left", "fmt": ""},
                    # {"x": clean.x[rightMainBeamLocs], "y": y_corrected[rightMainBeamLocs], "lab": "", "fmt": ""},
                    {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": "peak right", "fmt": ""},
                    {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": f"T$_A$ [K]: {ymax:.3f} +- {err_peakl:.3f}", "fmt": ""},
                    {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": f"T$_A$ [K]: {ymin:.3f} +- {err_peakr:.3f}", "fmt": ""},
                ],
                paths,
                log,
                save,
                plot_type="final",
                suffix="_corrected_final.png",
            )
            # sys.exit()
            # result.qc=qc
        return result

    else:
        log.debug("left: {:.3f}, min: {:.3f}, right: {:.3f}".format(
            ypeakl[0], ymin, ypeakl[-1]))
        log.debug("left: {:.3f}, max: {:.3f}, right{:.3f}".format(
            ypeakr[0], ymax, ypeakr[-1]))

        ypeakrdata = clean.x[rightMainBeamLocs]
        ypeakldata = clean.x[leftMainBeamLocs]

        # check data doesn't overlap
        overlapRight = set(baseLocsRight) & set(rightMainBeamLocs)
        overlapLeft = set(baseLocsLeft) & set(leftMainBeamLocs)
        # overlapbeams = set(leftMainBeamLocs) & set(rightMainBeamLocs)

        msg=("checking for overlapping beams: ")
        log.debug(msg)

        if len(overlapLeft) != 0:
            msg = "beams don't overlap on left"
            log.debug(msg)

            if leftMainBeamLocs[0] > baseLocsLeft[int(
                    len(baseLocsLeft)*.8)]:
                pass
            else:
                overlap = next(iter(overlapLeft))
                shift = list(leftMainBeamLocs).index(int(overlap))
                msg = "Overlap found on A beam"
                flag = 20
                log.warning(msg)

                # move beam to the left
                f = abs(len(leftMainBeamLocs)-shift)
                leftMainBeamLocs = abs(leftMainBeamLocs+f)

                # fit left peak
                ypeakl = np.polyval(np.polyfit(
                    clean.x[leftMainBeamLocs], y_corrected[leftMainBeamLocs],  2), clean.x[leftMainBeamLocs])
                fitResl, err_peakl = calc_residual(
                    y_corrected[leftMainBeamLocs], ypeakl)

                ymax = max(ypeakl)
                msg="left: {:.3f}, max: {:.3f}, right: {:.3f}".format(
                    ypeakl[0], ymax, ypeakl[-1])
                log.debug(msg)

                if(ypeakl[0] <= ymax or ypeakl[-1] <= ymax):
                    ymax = np.nan
                    err_peakl = np.nan
                else:
                    flag = 22
                    msg = "fit entire left beam"
                    log.debug(msg)

                ypeakldata = clean.x[leftMainBeamLocs]

                log.error(msg)
                plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
                result.flag = flag
                result.message = msg
                return result

        if len(overlapRight) != 0:

            overlap = next(iter(overlapRight))
            shift = list(rightMainBeamLocs).index(int(overlap))

            msg = "Overlap found on B beam"
            flag = 19
            log.warning( msg)

            # move beam to the RIGHT
            f = abs(len(rightMainBeamLocs)-shift)
            rightMainBeamLocs = abs(rightMainBeamLocs-f)

            msg="beam shifted to left by {} points".format(f)
            log.debug(msg)

            # fit right peak
            ypeakr = np.polyval(np.polyfit(
                clean.x[rightMainBeamLocs], y_corrected[rightMainBeamLocs],  2), clean.x[rightMainBeamLocs])
            fitResr, err_peakr = calc_residual(
                y_corrected[rightMainBeamLocs], ypeakr)

            ymin = min(ypeakr)

            msg="left: {:.3f}, min: {:.3f}, right{:.3f}".format(
                ypeakr[0], ymin, ypeakr[-1])
            log.debug(msg)

            if(ypeakr[0] <= ymin or ypeakr[-1] <= ymin):
                ymin = np.nan
                err_peakr = np.nan

            else:
                flag = 18
                msg = "fit entire right beam"
                log.debug(msg)

            # ypeakrdata = clean.x[rightMainBeamLocs]


            # return {"correctedData":[],"driftRes":[],"driftRms":np.nan,
            #             "driftCoeffs":[], "baseLocsCombined":[],
            #             "baseLocsLeft":[],"baseLocsRight":[],
            #         "leftPeakData":[],"leftPeakModelData":[],
            #         "leftPeakFit":np.nan, "leftPeakFitErr":np.nan,"leftPeakFitRes":[],
            #         "rightPeakData":[],"rightPeakModelData":[],
            #         "rightPeakFit":np.nan, "rightPeakFitErr":[],"rightPeakFitRes":[],
            #         "msg":"","midXValueLeft":[],"midXValueRight":[],
            #         "flag":flag
            #         }
            log.error(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result

        if ((x[leftMainBeamLocs])[-1] > 0):
            flag = 17
            msg = "left beam data goes beyond midpoint"
            log.warning(msg)
            # return {"correctedData":[],"driftRes":[],"driftRms":np.nan,
            #             "driftCoeffs":[], "baseLocsCombined":[],
            #             "baseLocsLeft":[],"baseLocsRight":[],
            #         "leftPeakData":[],"leftPeakModelData":[],
            #         "leftPeakFit":np.nan, "leftPeakFitErr":np.nan,"leftPeakFitRes":[],
            #         "rightPeakData":[],"rightPeakModelData":[],
            #         "rightPeakFit":np.nan, "rightPeakFitErr":[],"rightPeakFitRes":[],
            #         "msg":"","midXValueLeft":[],"midXValueRight":[],
            #         "flag":flag
            #         }
            # log.error(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result

        if ((x[rightMainBeamLocs])[-1] < 0):
            flag = 16
            msg = "right beam data goes beyond midpoint"
            log.warning(msg)
            # return [], [], [], np.nan, [], \
            #     [], [], np.nan, np.nan, [], \
            #     [], [], np.nan, np.nan, [],\
            #     msg, flag, np.nan, np.nan
            # return {"correctedData":[],"driftRes":[],"driftRms":np.nan,
            #             "driftCoeffs":[], "baseLocsCombined":[],
            #             "baseLocsLeft":[],"baseLocsRight":[],
            #         "leftPeakData":[],"leftPeakModelData":[],
            #         "leftPeakFit":np.nan, "leftPeakFitErr":np.nan,"leftPeakFitRes":[],
            #         "rightPeakData":[],"rightPeakModelData":[],
            #         "rightPeakFit":np.nan, "rightPeakFitErr":[],"rightPeakFitRes":[],
            #         "msg":"","midXValueLeft":[],"midXValueRight":[],
            #         "flag":flag
            #         }
            log.error(msg)
            plot_fail(x, y,paths,msg, log, save, flag=flag, fmt="orange")
            result.flag = flag
            result.message = msg
            return result
            


        log.info("\n")
        log.info("-"*30)
        log.info("Fit the peaks.")
        log.info("-"*30)

        msg="\npeak left: {:.3f} +- {:.3f} K\npeak right: {:.3f} +- {:.3f} K\n".format(
            ymin, err_peakl, ymax, err_peakr)
        log.info(msg)
      
        # find final peak loc
        ploca = np.where(ypeakl == ymin)[0]
        if len(ploca)==0:
            peakLoca=np.nan
        else:
            peakLoca = (x[leftMainBeamLocs])[ploca[0]]

        # find final peak loc
        plocb = np.where(ypeakr == ymax)[0] 
        if len(plocb)==0:    
            peakLocb=np.nan
        else:
            peakLocb = (x[rightMainBeamLocs])[plocb[0]]


        log.info('fit passed')
        # plot_fail(x, y,paths,msg, log, save, flag=30, fmt="orange")
        # result.apeak_coeffs =
        flag=0
        result.apeak_residuals = fitResl
        result.ata_peak = ymax
        result.ata_peak_err = err_peakl
        result.apeak_loc_index = peakLoca

        # result.bpeak_coeffs =
        result.bpeak_residuals = fitResr
        result.bta_peak = ymin
        result.bta_peak_err = err_peakr
        result.bpeak_loc_index = peakLocb

        result.baseline_coeffs = base_coeffs
        result.baseline_residuals = base_res
        result.baseline_rms = float(base_rms)
        result.baseline_window_indices = baseline_indices
        result.y_corrected = y_corrected
        result.y_corrected_spline = y_corr_spline

        result.clean_rms = clean.rms

        result.flag = flag
        result.message = msg

        a_idx = AbeamScan #np.where((x > -factored_fnbw) & (x < 0.0))[0]
        b_idx = BbeamScan #np.where((x > 0.0) & (x < factored_fnbw))[0]

        a_window = (float(x[a_idx[0]]), float(x[a_idx[-1]]))
        b_window = (float(x[b_idx[0]]), float(x[b_idx[-1]]))
        
        qc = compute_dual_beam_qc(
            x=x,
            y_corrected=y_corrected,
            baseline_sigma=float(base_rms),
            a_idx=a_idx,
            b_idx=b_idx,
            a_peak=float(result.ata_peak),
            a_peak_x=float(result.apeak_loc_index),
            a_resid=np.asarray(result.apeak_residuals) if result.apeak_residuals is not None else np.array([]),
            b_peak=float(result.bta_peak),
            b_peak_x=float(result.bpeak_loc_index),
            b_resid=np.asarray(result.bpeak_residuals) if result.bpeak_residuals is not None else np.array([]),
            a_window=a_window,
            b_window=b_window,
            cfg=cfg,
        )
        
        scan_qc = dual_beam_qc_to_scan_quality(qc)
        result.qc=scan_qc
        # print(qc);sys.exit()
        
        if qc.is_bad:
            result.flag = qc.flag
            result.message = "bad scan. " + " | ".join(qc.reasons)

            if qc.flag==60: 
                c = "fuchsia"
            elif qc.flag==61: 
                c = "r"
        
            # msg = "Failed QC"
            # print(qc.reasons)
            # sys.exit()
            # msg_wrapper("warning", log.warning, msg)
            # msg = "failed to locate base locs"
            log.error(msg)
            plot_fail(x, y,paths,result.message , log, save, flag=qc.flag, fmt=c)
            # result.flag = flag
            # result.message = msg
            
            return result

        else:
            result.flag = 0
            result.message = "ok"

        plot_diagnostics(
            [
                {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
                {"x": clean.x[leftMainBeamLocs], "y": y_corrected[leftMainBeamLocs], "lab": "peak left", "fmt": ""},
                {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": "peak left", "fmt": ""},
                {"x": clean.x[rightMainBeamLocs], "y": y_corrected[rightMainBeamLocs], "lab": "peak right", "fmt": ""},
                {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": "peak right", "fmt": ""},
                {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": f"T$_A$ [K]: {ymax:.3f} +- {err_peakl:.3f}", "fmt": ""},
                {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": f"T$_A$ [K]: {ymin:.3f} +- {err_peakr:.3f}", "fmt": ""},
            #     "\npeak left: {:.3f} +- {:.3f} K\npeak right: {:.3f} +- {:.3f} K\n".format(
            # ymax, err_peakl, ymin, err_peakr)
            ],
            paths,
            log,
            save,
            suffix="_corrected_final.png",
        )
        plot_diagnostics(
            [
                {"x": clean.x, "y": y_corrected, "lab": "corrected", "fmt": "k"},
                # {"x": clean.x[leftMainBeamLocs], "y": y_corrected[leftMainBeamLocs], "lab": "", "fmt": ""},
                {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": "peak left", "fmt": ""},
                # {"x": clean.x[rightMainBeamLocs], "y": y_corrected[rightMainBeamLocs], "lab": "", "fmt": ""},
                {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": "peak right", "fmt": ""},
                {"x": clean.x[leftMainBeamLocs], "y": ypeakl, "lab": f"T$_A$ [K]: {ymax:.3f} +- {err_peakl:.3f}", "fmt": ""},
                {"x": clean.x[rightMainBeamLocs], "y": ypeakr, "lab": f"T$_A$ [K]: {ymin:.3f} +- {err_peakr:.3f}", "fmt": ""},
            ],
            paths,
            log,
            save,
            plot_type="final",
            suffix="_corrected_final.png",
            
        )

        return result
