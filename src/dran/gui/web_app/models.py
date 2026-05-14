from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(np.asarray(value).item())
    except Exception:
        return default
    if not np.isfinite(number):
        return default
    return number


def jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return str(value)


@dataclass
class FitResult:
    scan_id: str
    scan_label: str
    fit_location: str
    fit_type: str
    fit_order: int
    selected_indices: list[int]
    coefficients: list[float]
    model_x: list[float]
    model_y: list[float]
    residual_x: list[float]
    residual_y: list[float]
    rms: float | None
    peak_value: float | None = None
    peak_x: float | None = None
    pss: float | None = None
    flux_density: float | None = None
    message: str = ""
    saved_at: str | None = None

    def as_record(self) -> dict[str, Any]:
        return jsonable(self.__dict__)


@dataclass
class ScanData:
    id: str
    label: str
    hdu_index: int
    hdu_name: str
    polarization: str
    x: np.ndarray
    y_raw: np.ndarray
    y_work: np.ndarray
    selected_indices: list[int] = field(default_factory=list)
    filtered_indices: list[int] = field(default_factory=list)
    baseline_result: FitResult | None = None
    peak_result: FitResult | None = None
    last_message: str = ""

    @property
    def point_count(self) -> int:
        return int(self.x.size)

    def reset(self) -> None:
        self.y_work = self.y_raw.copy()
        self.selected_indices.clear()
        self.filtered_indices.clear()
        self.baseline_result = None
        self.peak_result = None
        self.last_message = "Plot reset to raw data."

    def active_fit(self) -> FitResult | None:
        return self.peak_result or self.baseline_result


@dataclass
class ObservationSession:
    id: str
    source_path: Path
    filename: str
    metadata: dict[str, Any]
    scans: dict[str, ScanData]
    scan_order: list[str]
    selected_scan_id: str | None
    pss_options: list[dict[str, Any]] = field(default_factory=list)
    status: list[int] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0])
    saved_results: list[FitResult] = field(default_factory=list)
    messages: list[tuple[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def add_message(self, level: str, message: str) -> None:
        self.messages.append((level, message))
        self.messages = self.messages[-8:]

    @property
    def selected_scan(self) -> ScanData | None:
        if self.selected_scan_id is None:
            return None
        return self.scans.get(self.selected_scan_id)


@dataclass
class TimeSeriesSession:
    id: str
    db_path: Path
    tables: list[str]
    selected_table: str | None = None
    columns: list[str] = field(default_factory=list)
    numeric_columns: list[str] = field(default_factory=list)
    x_column: str | None = None
    y_column: str | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    hidden_rows: set[int] = field(default_factory=set)
    message: str = ""


@dataclass
class GallerySession:
    id: str
    directory: Path
    images: list[dict[str, Any]]
    message: str = ""
