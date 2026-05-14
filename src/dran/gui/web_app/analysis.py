from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from .models import FitResult, ScanData, safe_float


def nearest_indices(scan: ScanData, requested: list[int]) -> list[int]:
    max_index = scan.point_count - 1
    return sorted({min(max(int(idx), 0), max_index) for idx in requested if max_index >= 0})


def select_point(scan: ScanData, index: int) -> None:
    index = min(max(int(index), 0), scan.point_count - 1)
    if index in scan.selected_indices:
        scan.selected_indices.remove(index)
        scan.last_message = f"Removed point {index} from selection."
    else:
        scan.selected_indices.append(index)
        scan.selected_indices.sort()
        scan.last_message = f"Selected point {index}."


def smooth_scan(scan: ScanData, window: int) -> None:
    window = max(3, int(window))
    if window % 2 == 0:
        window += 1
    if scan.point_count < window:
        raise ValueError("Smoothing window is larger than the scan.")
    kernel = np.ones(window, dtype=float) / float(window)
    padded = np.pad(scan.y_work, (window // 2, window // 2), mode="edge")
    scan.y_work = np.convolve(padded, kernel, mode="valid")
    scan.filtered_indices.clear()
    scan.last_message = f"Applied smoothing with a {window}-sample window."


def rms_cut(scan: ScanData, sigma: float = 3.0) -> None:
    y = scan.y_work.astype(float)
    median = float(np.nanmedian(y))
    std = float(np.nanstd(y))
    if not math.isfinite(std) or std == 0.0:
        raise ValueError("RMS cut skipped because the scan has no measurable scatter.")
    mask = np.abs(y - median) > sigma * std
    indices = np.where(mask)[0]
    if indices.size == 0:
        scan.filtered_indices.clear()
        scan.last_message = "RMS cut found no outliers."
        return

    cleaned = y.copy()
    keep = ~mask
    cleaned[mask] = np.interp(scan.x[mask], scan.x[keep], y[keep])
    scan.y_work = cleaned
    scan.filtered_indices = [int(i) for i in indices.tolist()]
    scan.last_message = f"RMS cut replaced {len(indices)} outlier samples."


def fit_scan(
    scan: ScanData,
    fit_location: str,
    fit_type: str,
    fit_order: int,
) -> FitResult:
    fit_location = fit_location.lower().strip()
    fit_type = fit_type.lower().strip()
    fit_order = max(1, min(int(fit_order), 10))
    selected = nearest_indices(scan, scan.selected_indices)

    if fit_location == "base":
        result = _fit_baseline(scan, selected, fit_type, fit_order)
        scan.baseline_result = result
        scan.y_work = scan.y_work - np.asarray(result.model_y, dtype=float)
        scan.selected_indices.clear()
        scan.last_message = result.message
        return result

    if fit_location == "peak":
        result = _fit_peak(scan, selected, fit_type, fit_order)
        scan.peak_result = result
        scan.last_message = result.message
        return result

    raise ValueError(f"Unknown fit location: {fit_location}")


def _fit_baseline(scan: ScanData, selected: list[int], fit_type: str, fit_order: int) -> FitResult:
    if fit_type != "polynomial":
        fit_type = "polynomial"
    required = fit_order + 1
    if len(selected) < required:
        raise ValueError(f"Baseline fit needs at least {required} selected points for order {fit_order}.")

    x_sel = scan.x[selected]
    y_sel = scan.y_work[selected]
    coeffs = np.polyfit(x_sel, y_sel, fit_order)
    model = np.polyval(coeffs, scan.x)
    residual = y_sel - np.polyval(coeffs, x_sel)
    rms = _rms(residual)
    return FitResult(
        scan_id=scan.id,
        scan_label=scan.label,
        fit_location="Base",
        fit_type="Polynomial",
        fit_order=fit_order,
        selected_indices=selected,
        coefficients=[float(v) for v in coeffs],
        model_x=[float(v) for v in scan.x],
        model_y=[float(v) for v in model],
        residual_x=[float(v) for v in x_sel],
        residual_y=[float(v) for v in residual],
        rms=rms,
        message=f"Baseline corrected with an order {fit_order} polynomial.",
    )


def _fit_peak(scan: ScanData, selected: list[int], fit_type: str, fit_order: int) -> FitResult:
    if len(selected) < 3:
        selected = _default_peak_window(scan)
    if len(selected) < 3:
        raise ValueError("Peak fit needs at least 3 selected points.")

    x_sel = scan.x[selected]
    y_sel = scan.y_work[selected]
    if fit_type == "gaussian":
        result = _fit_gaussian_peak(scan, selected, x_sel, y_sel)
        if result is not None:
            return result

    order = max(2, min(fit_order, len(selected) - 1))
    coeffs = np.polyfit(x_sel, y_sel, order)
    x_model = np.linspace(float(np.min(x_sel)), float(np.max(x_sel)), 240)
    y_model = np.polyval(coeffs, x_model)
    selected_model = np.polyval(coeffs, x_sel)
    residual = y_sel - selected_model
    peak_idx = int(np.nanargmax(y_model))
    return FitResult(
        scan_id=scan.id,
        scan_label=scan.label,
        fit_location="Peak",
        fit_type="Polynomial",
        fit_order=order,
        selected_indices=selected,
        coefficients=[float(v) for v in coeffs],
        model_x=[float(v) for v in x_model],
        model_y=[float(v) for v in y_model],
        residual_x=[float(v) for v in x_sel],
        residual_y=[float(v) for v in residual],
        rms=_rms(residual),
        peak_value=safe_float(y_model[peak_idx]),
        peak_x=safe_float(x_model[peak_idx]),
        message=f"Peak fitted with an order {order} polynomial.",
    )


def _fit_gaussian_peak(scan: ScanData, selected: list[int], x_sel: np.ndarray, y_sel: np.ndarray) -> FitResult | None:
    floor = float(np.nanmin(y_sel))
    positive = y_sel - floor
    positive = np.where(positive <= 0, np.nan, positive)
    if np.count_nonzero(np.isfinite(positive)) < 3:
        return None

    try:
        coeffs = np.polyfit(x_sel[np.isfinite(positive)], np.log(positive[np.isfinite(positive)]), 2)
    except Exception:
        return None
    a, b, c = [float(v) for v in coeffs]
    if a >= 0:
        return None

    mu = -b / (2.0 * a)
    sigma = math.sqrt(-1.0 / (2.0 * a))
    amp = math.exp(c - a * mu * mu)
    x_model = np.linspace(float(np.min(x_sel)), float(np.max(x_sel)), 240)
    y_model = floor + amp * np.exp(-0.5 * ((x_model - mu) / sigma) ** 2)
    selected_model = floor + amp * np.exp(-0.5 * ((x_sel - mu) / sigma) ** 2)
    residual = y_sel - selected_model
    peak_idx = int(np.nanargmax(y_model))
    return FitResult(
        scan_id=scan.id,
        scan_label=scan.label,
        fit_location="Peak",
        fit_type="Gaussian",
        fit_order=2,
        selected_indices=selected,
        coefficients=[amp, mu, sigma, floor],
        model_x=[float(v) for v in x_model],
        model_y=[float(v) for v in y_model],
        residual_x=[float(v) for v in x_sel],
        residual_y=[float(v) for v in residual],
        rms=_rms(residual),
        peak_value=safe_float(y_model[peak_idx]),
        peak_x=safe_float(x_model[peak_idx]),
        message="Peak fitted with a log-linear Gaussian estimate.",
    )


def _default_peak_window(scan: ScanData) -> list[int]:
    if scan.point_count < 3:
        return []
    peak_index = int(np.nanargmax(scan.y_work))
    width = max(2, scan.point_count // 20)
    start = max(0, peak_index - width)
    stop = min(scan.point_count, peak_index + width + 1)
    return list(range(start, stop))


def _rms(values: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return None
    return safe_float(np.sqrt(np.nanmean(values ** 2)))


def save_current_fit(scan: ScanData) -> FitResult:
    result = scan.active_fit()
    if result is None:
        raise ValueError("There is no fit to save for the current scan.")
    clone = FitResult(**result.as_record())
    clone.saved_at = datetime.utcnow().isoformat(timespec="seconds")
    return clone


def apply_pss(scan: ScanData, pss_value: float) -> FitResult:
    if pss_value == 0:
        raise ValueError("PSS must be non-zero.")
    result = scan.peak_result
    if result is None or result.peak_value is None:
        raise ValueError("Fit a peak before calculating flux density.")
    result.pss = float(pss_value)
    result.flux_density = float(result.peak_value) / float(pss_value)
    result.message = f"Flux density calculated with PSS={pss_value:.6g}."
    return result
