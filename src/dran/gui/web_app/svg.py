from __future__ import annotations

from html import escape
from typing import Iterable

import numpy as np

from .models import FitResult, ScanData, TimeSeriesSession


def _finite_range(values: Iterable[float], pad_fraction: float = 0.08) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return -1.0, 1.0
    low = float(np.nanmin(arr))
    high = float(np.nanmax(arr))
    if low == high:
        pad = abs(low) * 0.1 or 1.0
        return low - pad, high + pad
    pad = (high - low) * pad_fraction
    return low - pad, high + pad


def _polyline(x: np.ndarray, y: np.ndarray, tx, ty, max_points: int = 1400) -> str:
    if x.size == 0:
        return ""
    step = max(1, int(np.ceil(x.size / max_points)))
    points = " ".join(f"{tx(float(a)):.2f},{ty(float(b)):.2f}" for a, b in zip(x[::step], y[::step]))
    return points


def _ticks(low: float, high: float, count: int = 5) -> list[float]:
    return [float(v) for v in np.linspace(low, high, count)]


def scan_svg(session_id: str, scan: ScanData) -> str:
    width = 900
    height = 500
    margin_left = 62
    margin_right = 24
    main_top = 24
    main_height = 310
    gap = 42
    residual_top = main_top + main_height + gap
    residual_height = 90
    plot_width = width - margin_left - margin_right

    fit = scan.active_fit()
    model_x = np.asarray(fit.model_x, dtype=float) if fit else np.array([])
    model_y = np.asarray(fit.model_y, dtype=float) if fit else np.array([])

    xmin, xmax = _finite_range(scan.x)
    y_values = list(scan.y_work)
    if model_y.size:
        y_values.extend(model_y.tolist())
    ymin, ymax = _finite_range(y_values)

    def tx(value: float) -> float:
        return margin_left + (value - xmin) / (xmax - xmin) * plot_width

    def ty(value: float) -> float:
        return main_top + main_height - (value - ymin) / (ymax - ymin) * main_height

    elements: list[str] = [
        f'<svg class="plot-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(scan.label)}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" class="plot-bg"/>',
        f'<rect x="{margin_left}" y="{main_top}" width="{plot_width}" height="{main_height}" class="plot-panel"/>',
    ]

    for tick in _ticks(xmin, xmax):
        x_pos = tx(tick)
        elements.append(f'<line x1="{x_pos:.2f}" y1="{main_top}" x2="{x_pos:.2f}" y2="{main_top + main_height}" class="grid-line"/>')
        elements.append(f'<text x="{x_pos:.2f}" y="{main_top + main_height + 24}" class="axis-text" text-anchor="middle">{tick:.3g}</text>')

    for tick in _ticks(ymin, ymax):
        y_pos = ty(tick)
        elements.append(f'<line x1="{margin_left}" y1="{y_pos:.2f}" x2="{margin_left + plot_width}" y2="{y_pos:.2f}" class="grid-line"/>')
        elements.append(f'<text x="{margin_left - 10}" y="{y_pos + 4:.2f}" class="axis-text" text-anchor="end">{tick:.3g}</text>')

    if ymin <= 0 <= ymax:
        zero_y = ty(0.0)
        elements.append(f'<line x1="{margin_left}" y1="{zero_y:.2f}" x2="{margin_left + plot_width}" y2="{zero_y:.2f}" class="zero-line"/>')

    line_points = _polyline(scan.x, scan.y_work, tx, ty)
    elements.append(f'<polyline points="{line_points}" class="data-line"/>')

    if model_x.size and model_y.size:
        model_points = _polyline(model_x, model_y, tx, ty, max_points=900)
        elements.append(f'<polyline points="{model_points}" class="fit-line"/>')

    step = max(1, int(np.ceil(scan.point_count / 850)))
    selected = set(scan.selected_indices)
    filtered = set(scan.filtered_indices)
    rendered = set(range(0, scan.point_count, step)) | selected | filtered
    for idx in sorted(rendered):
        x_val = float(scan.x[idx])
        y_val = float(scan.y_work[idx])
        css = "pick-point"
        radius = 3.2
        if idx in filtered:
            css += " filtered-point"
            radius = 4.4
        if idx in selected:
            css += " selected-point"
            radius = 5.8
        elements.append(
            (
                f'<circle cx="{tx(x_val):.2f}" cy="{ty(y_val):.2f}" r="{radius}" class="{css}" '
                f'hx-post="/drift/select-point?session_id={escape(session_id)}&index={idx}" '
                'hx-target="#workspace" hx-swap="outerHTML">'
                f'<title>index {idx}: x={x_val:.6g}, y={y_val:.6g}</title></circle>'
            )
        )

    elements.append(f'<text x="{margin_left + plot_width / 2:.2f}" y="{height - 10}" class="axis-label" text-anchor="middle">Scan distance / sample axis</text>')
    elements.append(f'<text transform="translate(18,{main_top + main_height / 2:.2f}) rotate(-90)" class="axis-label" text-anchor="middle">Ta / relative K</text>')
    elements.append(f'<text x="{margin_left}" y="16" class="plot-title">{escape(scan.label)}</text>')

    if fit:
        elements.extend(_residual_svg(fit, margin_left, residual_top, plot_width, residual_height))

    elements.append("</svg>")
    return "".join(elements)


def _residual_svg(fit: FitResult, left: int, top: int, width: int, height: int) -> list[str]:
    x = np.asarray(fit.residual_x, dtype=float)
    y = np.asarray(fit.residual_y, dtype=float)
    if x.size == 0 or y.size == 0:
        return []
    xmin, xmax = _finite_range(x)
    ymin, ymax = _finite_range(y)

    def tx(value: float) -> float:
        return left + (value - xmin) / (xmax - xmin) * width

    def ty(value: float) -> float:
        return top + height - (value - ymin) / (ymax - ymin) * height

    elements = [
        f'<rect x="{left}" y="{top}" width="{width}" height="{height}" class="plot-panel residual-panel"/>',
        f'<text x="{left}" y="{top - 8}" class="plot-subtitle">Residuals</text>',
    ]
    if ymin <= 0 <= ymax:
        zero_y = ty(0.0)
        elements.append(f'<line x1="{left}" y1="{zero_y:.2f}" x2="{left + width}" y2="{zero_y:.2f}" class="zero-line"/>')
    points = _polyline(x, y, tx, ty, max_points=500)
    elements.append(f'<polyline points="{points}" class="residual-line"/>')
    return elements


def time_series_svg(ts: TimeSeriesSession) -> str:
    width = 860
    height = 440
    left = 62
    top = 24
    plot_width = width - left - 28
    plot_height = height - top - 56

    if not ts.rows or not ts.x_column or not ts.y_column:
        return '<div class="empty-state">Open a database table and choose X/Y columns.</div>'

    xs = np.asarray([_coerce(row.get(ts.x_column)) for row in ts.rows], dtype=float)
    ys = np.asarray([_coerce(row.get(ts.y_column)) for row in ts.rows], dtype=float)
    finite = np.isfinite(xs) & np.isfinite(ys)
    xmin, xmax = _finite_range(xs[finite])
    ymin, ymax = _finite_range(ys[finite])

    def tx(value: float) -> float:
        return left + (value - xmin) / (xmax - xmin) * plot_width

    def ty(value: float) -> float:
        return top + plot_height - (value - ymin) / (ymax - ymin) * plot_height

    elements = [
        f'<svg class="plot-svg" viewBox="0 0 {width} {height}" role="img" aria-label="time series">',
        f'<rect x="0" y="0" width="{width}" height="{height}" class="plot-bg"/>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" class="plot-panel"/>',
    ]
    for tick in _ticks(xmin, xmax):
        x_pos = tx(tick)
        elements.append(f'<line x1="{x_pos:.2f}" y1="{top}" x2="{x_pos:.2f}" y2="{top + plot_height}" class="grid-line"/>')
        elements.append(f'<text x="{x_pos:.2f}" y="{top + plot_height + 24}" class="axis-text" text-anchor="middle">{tick:.3g}</text>')
    for tick in _ticks(ymin, ymax):
        y_pos = ty(tick)
        elements.append(f'<line x1="{left}" y1="{y_pos:.2f}" x2="{left + plot_width}" y2="{y_pos:.2f}" class="grid-line"/>')
        elements.append(f'<text x="{left - 10}" y="{y_pos + 4:.2f}" class="axis-text" text-anchor="end">{tick:.3g}</text>')

    for idx, (x_val, y_val, ok) in enumerate(zip(xs, ys, finite)):
        if not ok:
            continue
        css = "ts-point muted-point" if idx in ts.hidden_rows else "ts-point"
        elements.append(
            f'<circle cx="{tx(float(x_val)):.2f}" cy="{ty(float(y_val)):.2f}" r="4.6" class="{css}" '
            f'hx-post="/timeseries/toggle?session_id={escape(ts.id)}&row_index={idx}" '
            'hx-target="#timeseries-panel" hx-swap="outerHTML">'
            f'<title>row {idx}: {escape(ts.x_column)}={x_val:.6g}, {escape(ts.y_column)}={y_val:.6g}</title></circle>'
        )
    elements.append(f'<text x="{left + plot_width / 2:.2f}" y="{height - 10}" class="axis-label" text-anchor="middle">{escape(ts.x_column)}</text>')
    elements.append(f'<text transform="translate(18,{top + plot_height / 2:.2f}) rotate(-90)" class="axis-label" text-anchor="middle">{escape(ts.y_column)}</text>')
    elements.append("</svg>")
    return "".join(elements)


def _coerce(value) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")
