from __future__ import annotations

import argparse
import html
import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

SRC_ROOT = Path(__file__).resolve().parents[3]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from .analysis import apply_pss, fit_scan, rms_cut, save_current_fit, select_point, smooth_scan
from .fits_io import load_observation
from .models import GallerySession, TimeSeriesSession, new_id, safe_float
from .store import (
    get_gallery,
    get_observation,
    get_time_series,
    remember_gallery,
    remember_observation,
    remember_time_series,
    runtime_dir,
    save_observation_to_db,
    upload_dir,
)
from .svg import scan_svg, time_series_svg


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def fmt(value: Any, precision: int = 5) -> str:
    if value is None:
        return ""
    number = safe_float(value)
    if number is not None:
        return f"{number:.{precision}g}"
    return html.escape(str(value))


templates.env.filters["fmt"] = fmt


def create_app() -> FastAPI:
    app = FastAPI(title="DRAN standalone web GUI")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    register_routes(app)
    return app


def sample_fits_files() -> list[Path]:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    if not data_dir.exists():
        return []
    return sorted(data_dir.rglob("*.fits"))[:12]


def render_index(request: Request, **context: Any):
    context.setdefault("samples", sample_fits_files())
    context.setdefault("runtime_dir", runtime_dir())
    return templates.TemplateResponse(request, "index.html", context)


def render_workspace(request: Request, session_id: str | None, status_code: int = 200):
    session = get_observation(session_id)
    plot_svg = ""
    if session and session.selected_scan:
        plot_svg = scan_svg(session.id, session.selected_scan)
    return templates.TemplateResponse(
        request,
        "partials/workspace.html",
        {"session": session, "plot_svg": plot_svg},
        status_code=status_code,
    )


def render_timeseries(request: Request, session_id: str | None):
    ts = get_time_series(session_id)
    svg = time_series_svg(ts) if ts else ""
    return templates.TemplateResponse(
        request,
        "partials/timeseries.html",
        {"timeseries": ts, "timeseries_svg": svg},
    )


def render_gallery(request: Request, session_id: str | None):
    gallery = get_gallery(session_id)
    return templates.TemplateResponse(
        request,
        "partials/gallery.html",
        {"gallery": gallery},
    )


def register_routes(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return render_index(request)

    @app.post("/drift/open-path", response_class=HTMLResponse)
    async def open_path(request: Request, path: str = Form(...)):
        try:
            session = load_observation(Path(path))
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "partials/workspace.html",
                {"session": None, "plot_svg": "", "error": str(exc)},
                status_code=400,
            )
        session.status[0] = 1
        remember_observation(session)
        return render_workspace(request, session.id)

    @app.post("/drift/upload", response_class=HTMLResponse)
    async def upload_fits(request: Request, file: UploadFile = File(...)):
        filename = Path(file.filename or "upload.fits").name
        target = upload_dir() / filename
        target.write_bytes(await file.read())
        try:
            session = load_observation(target)
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "partials/workspace.html",
                {"session": None, "plot_svg": "", "error": str(exc)},
                status_code=400,
            )
        session.status[0] = 1
        remember_observation(session)
        return render_workspace(request, session.id)

    @app.post("/drift/select-scan", response_class=HTMLResponse)
    async def select_scan(request: Request, session_id: str = Form(...), scan_id: str = Form(...)):
        session = require_observation(session_id)
        if scan_id not in session.scans:
            raise HTTPException(status_code=404, detail="Unknown scan selection.")
        session.selected_scan_id = scan_id
        session.add_message("info", f"Selected {session.scans[scan_id].label}.")
        return render_workspace(request, session.id)

    @app.post("/drift/select-point", response_class=HTMLResponse)
    async def choose_point(request: Request, session_id: str, index: int):
        session = require_observation(session_id)
        scan = require_scan(session)
        select_point(scan, index)
        session.status[1] = 1 if scan.selected_indices else 0
        session.add_message("info", scan.last_message)
        return render_workspace(request, session.id)

    @app.post("/drift/clear-selection", response_class=HTMLResponse)
    async def clear_selection(request: Request, session_id: str = Form(...)):
        session = require_observation(session_id)
        scan = require_scan(session)
        scan.selected_indices.clear()
        session.status[1] = 0
        session.add_message("info", "Selection cleared.")
        return render_workspace(request, session.id)

    @app.post("/drift/filter", response_class=HTMLResponse)
    async def filter_data(
        request: Request,
        session_id: str = Form(...),
        filter_type: str = Form("Smoothing"),
        window: int = Form(9),
    ):
        session = require_observation(session_id)
        scan = require_scan(session)
        try:
            if filter_type == "Rms cuts":
                rms_cut(scan)
            else:
                smooth_scan(scan, window)
            session.status[2] = 1
            session.add_message("info", scan.last_message)
        except Exception as exc:
            session.add_message("error", str(exc))
        return render_workspace(request, session.id)

    @app.post("/drift/fit", response_class=HTMLResponse)
    async def fit_data(
        request: Request,
        session_id: str = Form(...),
        fit_type: str = Form("Polynomial"),
        fit_location: str = Form("Base"),
        fit_order: int = Form(1),
    ):
        session = require_observation(session_id)
        scan = require_scan(session)
        try:
            result = fit_scan(scan, fit_location, fit_type, fit_order)
            if result.fit_location == "Base":
                session.status[3] = 1
            else:
                session.status[4] = 1
            session.add_message("info", result.message)
        except Exception as exc:
            session.add_message("error", str(exc))
        return render_workspace(request, session.id)

    @app.post("/drift/calculate-flux", response_class=HTMLResponse)
    async def calculate_flux(request: Request, session_id: str = Form(...), pss: float = Form(...)):
        session = require_observation(session_id)
        scan = require_scan(session)
        try:
            result = apply_pss(scan, pss)
            session.add_message("info", result.message)
        except Exception as exc:
            session.add_message("error", str(exc))
        return render_workspace(request, session.id)

    @app.post("/drift/save-fit", response_class=HTMLResponse)
    async def save_fit(request: Request, session_id: str = Form(...)):
        session = require_observation(session_id)
        scan = require_scan(session)
        try:
            saved = save_current_fit(scan)
            session.saved_results.append(saved)
            session.status[5] = 1
            session.add_message("info", f"Saved {saved.fit_location.lower()} fit for {scan.label} in this session.")
        except Exception as exc:
            session.add_message("error", str(exc))
        return render_workspace(request, session.id)

    @app.post("/drift/save-db", response_class=HTMLResponse)
    async def save_db(request: Request, session_id: str = Form(...)):
        session = require_observation(session_id)
        try:
            count = save_observation_to_db(session)
            session.add_message("info", f"Wrote {count} fit result(s) to {runtime_dir() / 'dran_gui_web.sqlite'}.")
        except Exception as exc:
            session.add_message("error", str(exc))
        return render_workspace(request, session.id)

    @app.post("/drift/reset-plot", response_class=HTMLResponse)
    async def reset_plot(request: Request, session_id: str = Form(...)):
        session = require_observation(session_id)
        scan = require_scan(session)
        scan.reset()
        session.status[1:5] = [0, 0, 0, 0]
        session.add_message("info", scan.last_message)
        return render_workspace(request, session.id)

    @app.post("/drift/reset-status", response_class=HTMLResponse)
    async def reset_status(request: Request, session_id: str = Form(...)):
        session = require_observation(session_id)
        session.status = [1, 0, 0, 0, 0, 0]
        session.add_message("info", "Status reset for the current observation.")
        return render_workspace(request, session.id)

    @app.post("/timeseries/open", response_class=HTMLResponse)
    async def open_timeseries(request: Request, path: str = Form(...)):
        try:
            ts = load_time_series(Path(path))
            remember_time_series(ts)
        except Exception as exc:
            ts = None
            return templates.TemplateResponse(
                request,
                "partials/timeseries.html",
                {"timeseries": ts, "timeseries_svg": "", "error": str(exc)},
                status_code=400,
            )
        return render_timeseries(request, ts.id)

    @app.post("/timeseries/upload", response_class=HTMLResponse)
    async def upload_timeseries(request: Request, file: UploadFile = File(...)):
        filename = Path(file.filename or "database.sqlite").name
        target = upload_dir() / filename
        target.write_bytes(await file.read())
        try:
            ts = load_time_series(target)
            remember_time_series(ts)
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "partials/timeseries.html",
                {"timeseries": None, "timeseries_svg": "", "error": str(exc)},
                status_code=400,
            )
        return render_timeseries(request, ts.id)

    @app.post("/timeseries/plot", response_class=HTMLResponse)
    async def plot_timeseries(
        request: Request,
        session_id: str = Form(...),
        table: str = Form(...),
        x_column: str = Form(...),
        y_column: str = Form(...),
    ):
        ts = require_time_series(session_id)
        try:
            refresh_time_series(ts, table, x_column, y_column)
        except Exception as exc:
            ts.message = str(exc)
        return render_timeseries(request, ts.id)

    @app.post("/timeseries/toggle", response_class=HTMLResponse)
    async def toggle_timeseries_point(request: Request, session_id: str, row_index: int):
        ts = require_time_series(session_id)
        if row_index in ts.hidden_rows:
            ts.hidden_rows.remove(row_index)
            ts.message = f"Restored row {row_index}."
        else:
            ts.hidden_rows.add(row_index)
            ts.message = f"Marked row {row_index} as hidden for this session."
        return render_timeseries(request, ts.id)

    @app.post("/gallery/open", response_class=HTMLResponse)
    async def open_gallery(request: Request, path: str = Form(...)):
        try:
            gallery = load_gallery(Path(path))
            remember_gallery(gallery)
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "partials/gallery.html",
                {"gallery": None, "error": str(exc)},
                status_code=400,
            )
        return render_gallery(request, gallery.id)

    @app.get("/gallery/image")
    async def gallery_image(session_id: str, index: int):
        gallery = get_gallery(session_id)
        if gallery is None or index < 0 or index >= len(gallery.images):
            raise HTTPException(status_code=404, detail="Image not found.")
        return FileResponse(gallery.images[index]["path"])

    @app.get("/favicon.ico")
    async def favicon():
        return RedirectResponse(url="/static/favicon.svg")


def require_observation(session_id: str):
    session = get_observation(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Observation session not found.")
    return session


def require_scan(session):
    scan = session.selected_scan
    if scan is None:
        raise HTTPException(status_code=404, detail="No scan selected.")
    return scan


def require_time_series(session_id: str) -> TimeSeriesSession:
    session = get_time_series(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Time-series session not found.")
    return session


def load_time_series(path: Path) -> TimeSeriesSession:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database does not exist: {path}")
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
    if not tables:
        raise ValueError("No user tables found in the database.")
    ts = TimeSeriesSession(id=new_id("ts"), db_path=path, tables=tables)
    refresh_time_series(ts, tables[0], "", "")
    ts.message = f"Opened {path.name}."
    return ts


def refresh_time_series(ts: TimeSeriesSession, table: str, x_column: str, y_column: str) -> None:
    if table not in ts.tables:
        raise ValueError(f"Unknown table: {table}")
    with sqlite3.connect(ts.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(f'SELECT * FROM "{table}" LIMIT 2000')]
        columns = [row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')]

    numeric_columns = _numeric_columns(rows, columns)
    if not numeric_columns:
        raise ValueError(f"Table {table} has no numeric columns to plot.")
    ts.selected_table = table
    ts.columns = columns
    ts.numeric_columns = numeric_columns
    ts.rows = rows
    ts.x_column = x_column if x_column in columns else numeric_columns[0]
    fallback_y = numeric_columns[1] if len(numeric_columns) > 1 else numeric_columns[0]
    ts.y_column = y_column if y_column in columns else fallback_y
    ts.message = f"Loaded {len(rows)} rows from {table}."


def _numeric_columns(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    numeric: list[str] = []
    sample = rows[:50]
    for col in columns:
        values = [row.get(col) for row in sample if row.get(col) is not None]
        if values and any(_is_number(v) for v in values):
            numeric.append(col)
    return numeric


def _is_number(value: Any) -> bool:
    try:
        number = float(value)
    except Exception:
        return False
    return np.isfinite(number)


def load_gallery(path: Path) -> GallerySession:
    path = path.expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Plot directory does not exist: {path}")
    exts = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    files = [p for p in sorted(path.rglob("*")) if p.suffix.lower() in exts]
    images = [
        {
            "path": str(p),
            "name": p.name,
            "relative": str(p.relative_to(path)),
        }
        for p in files[:300]
    ]
    return GallerySession(
        id=new_id("gallery"),
        directory=path,
        images=images,
        message=f"Found {len(images)} image(s) under {path}.",
    )


app = create_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the standalone DRAN web GUI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    import uvicorn

    uvicorn.run("dran.gui.web_app.app:app", host=args.host, port=args.port, reload=args.reload)
