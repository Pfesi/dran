from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import GallerySession, ObservationSession, TimeSeriesSession


OBSERVATIONS: dict[str, ObservationSession] = {}
TIME_SERIES: dict[str, TimeSeriesSession] = {}
GALLERIES: dict[str, GallerySession] = {}


def runtime_dir() -> Path:
    base = Path(os.environ.get("DRAN_WEB_DATA_DIR", "/tmp/dran_gui_web_results"))
    base.mkdir(parents=True, exist_ok=True)
    (base / "uploads").mkdir(parents=True, exist_ok=True)
    return base


def upload_dir() -> Path:
    path = runtime_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return runtime_dir() / "dran_gui_web.sqlite"


def remember_observation(session: ObservationSession) -> None:
    OBSERVATIONS[session.id] = session


def get_observation(session_id: str | None) -> ObservationSession | None:
    if not session_id:
        return None
    return OBSERVATIONS.get(session_id)


def remember_time_series(session: TimeSeriesSession) -> None:
    TIME_SERIES[session.id] = session


def get_time_series(session_id: str | None) -> TimeSeriesSession | None:
    if not session_id:
        return None
    return TIME_SERIES.get(session_id)


def remember_gallery(session: GallerySession) -> None:
    GALLERIES[session.id] = session


def get_gallery(session_id: str | None) -> GallerySession | None:
    if not session_id:
        return None
    return GALLERIES.get(session_id)


def save_observation_to_db(session: ObservationSession) -> int:
    path = database_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fit_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at TEXT NOT NULL,
                session_id TEXT NOT NULL,
                source_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                scan_label TEXT NOT NULL,
                fit_location TEXT NOT NULL,
                fit_type TEXT NOT NULL,
                fit_order INTEGER NOT NULL,
                rms REAL,
                peak_value REAL,
                peak_x REAL,
                pss REAL,
                flux_density REAL,
                selected_indices TEXT NOT NULL,
                coefficients TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )

        inserted = 0
        for result in session.saved_results:
            record: dict[str, Any] = result.as_record()
            conn.execute(
                """
                INSERT INTO fit_results (
                    saved_at, session_id, source_path, filename, scan_id,
                    scan_label, fit_location, fit_type, fit_order, rms,
                    peak_value, peak_x, pss, flux_density, selected_indices,
                    coefficients, result_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    session.id,
                    str(session.source_path),
                    session.filename,
                    result.scan_id,
                    result.scan_label,
                    result.fit_location,
                    result.fit_type,
                    result.fit_order,
                    result.rms,
                    result.peak_value,
                    result.peak_x,
                    result.pss,
                    result.flux_density,
                    json.dumps(result.selected_indices),
                    json.dumps(result.coefficients),
                    json.dumps(record),
                ),
            )
            inserted += 1

    return inserted
