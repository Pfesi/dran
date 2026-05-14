from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits

from dran.fits.conversion import counts_to_kelvin

from .models import ObservationSession, ScanData, new_id, safe_float


METADATA_KEYS = {
    "date": ("DATE",),
    "observer": ("OBSERVER",),
    "object_name": ("OBJECT",),
    "frequency_mhz": ("CENTFREQ", "CENTFRQ1"),
    "temperature_k": ("TAMBIENT", "TEMP"),
    "pressure_hpa": ("PRESSURE", "PRESS"),
    "humidity_pct": ("HUMIDITY", "HUM"),
    "hpbw_deg": ("HPBW",),
    "fnbw_deg": ("FNBW",),
    "scan_distance_deg": ("SCANDIST",),
    "frontend": ("FRONTEND",),
    "bandwidth_mhz": ("BANDWDTH", "BANDWIDTH"),
}


def _header_value(hdul: fits.HDUList, names: tuple[str, ...]) -> Any:
    for hdu in hdul:
        for name in names:
            value = hdu.header.get(name)
            if value is not None:
                return value
    return None


def _metadata(hdul: fits.HDUList, path: Path) -> dict[str, Any]:
    meta = {field: _header_value(hdul, keys) for field, keys in METADATA_KEYS.items()}
    date_value = str(meta.get("date") or "")
    if "T" in date_value:
        meta["obs_date"], meta["obs_time"] = date_value.split("T", 1)
    else:
        meta["obs_date"] = date_value or None
        meta["obs_time"] = None
    meta["filename"] = path.name
    meta["path"] = str(path)
    return meta


def _table_names(data: Any) -> list[str]:
    names = getattr(data, "names", None)
    if names is None and hasattr(data, "dtype"):
        names = data.dtype.names
    return list(names or [])


def _best_scale(hdul: fits.HDUList, header: fits.Header, key: str) -> float | None:
    value = safe_float(header.get(key))
    if value not in (None, 0.0):
        return value

    # The calibration scale can live in a calibration or Chart HDU, depending
    # on frontend/band. Prefer the last occurrence because many legacy files
    # store the final usable value there.
    candidates: list[float] = []
    for hdu in hdul:
        candidate = safe_float(hdu.header.get(key))
        if candidate not in (None, 0.0):
            candidates.append(candidate)
    return candidates[-1] if candidates else None


def _offset_axis(header: fits.Header, primary_header: fits.Header, count: int) -> np.ndarray:
    scan_dist = safe_float(header.get("SCANDIST"))
    if scan_dist in (None, 0.0):
        scan_dist = safe_float(primary_header.get("SCANDIST"))
    if scan_dist in (None, 0.0):
        return np.arange(count, dtype=float)
    return np.linspace(-scan_dist / 2.0, scan_dist / 2.0, count)


def _series_from_counts(hdul: fits.HDUList, hdu: fits.BinTableHDU, column: str) -> np.ndarray:
    counts = np.asarray(hdu.data[column], dtype=float).ravel()
    scale_key = "HZPERK1" if column == "Count1" else "HZPERK2"
    scale = _best_scale(hdul, hdu.header, scale_key)
    if scale not in (None, 0.0):
        converted = np.asarray(counts_to_kelvin(counts, scale), dtype=float)
        if np.any(np.isfinite(converted)) and not np.allclose(converted, 0.0):
            return converted

    # Fallback keeps the scan useful when no diode scale is present.
    if counts.size:
        return counts - float(counts[0])
    return counts


def _midpoint_value(hdu: fits.BinTableHDU, name: str) -> float | None:
    names = _table_names(hdu.data)
    if name not in names:
        return None
    values = np.asarray(hdu.data[name]).ravel()
    if values.size == 0:
        return None
    return safe_float(values[values.size // 2])


def load_observation(path: Path) -> ObservationSession:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"FITS file does not exist: {path}")
    if path.suffix.lower() not in {".fits", ".fit", ".fts"}:
        raise ValueError(f"Expected a FITS file, got: {path.name}")

    with fits.open(path, memmap=True) as hdul:
        metadata = _metadata(hdul, path)
        scans: dict[str, ScanData] = {}
        order: list[str] = []
        primary_header = hdul[0].header if hdul else fits.Header()

        # Prefer central scan values for display metadata when present.
        for hdu in hdul:
            if not isinstance(hdu, fits.BinTableHDU) or hdu.data is None:
                continue
            names = _table_names(hdu.data)
            if "Hour_Angle" in names and metadata.get("ha") is None:
                metadata["ha"] = _midpoint_value(hdu, "Hour_Angle")
            if "Elevation" in names and metadata.get("za") is None:
                elevation = _midpoint_value(hdu, "Elevation")
                metadata["za"] = 90.0 - elevation if elevation is not None else None
            if "MJD" in names and metadata.get("mjd") is None:
                metadata["mjd"] = _midpoint_value(hdu, "MJD")

        for hdu_index, hdu in enumerate(hdul):
            if not isinstance(hdu, fits.BinTableHDU) or hdu.data is None:
                continue
            names = _table_names(hdu.data)
            count_columns = [name for name in ("Count1", "Count2") if name in names]
            if not count_columns:
                continue

            for column in count_columns:
                y = _series_from_counts(hdul, hdu, column)
                x = _offset_axis(hdu.header, primary_header, y.size)
                pol = "LCP" if column == "Count1" else "RCP"
                scan_id = f"hdu{hdu_index}_{column.lower()}"
                label = f"HDU {hdu_index}: {hdu.name} {pol}"
                scans[scan_id] = ScanData(
                    id=scan_id,
                    label=label,
                    hdu_index=hdu_index,
                    hdu_name=hdu.name,
                    polarization=pol,
                    x=x,
                    y_raw=y,
                    y_work=y.copy(),
                )
                order.append(scan_id)

        if not scans:
            raise ValueError("No scan HDUs with Count1/Count2 columns were found.")

        pss_options = _pss_options(hdul)

    session = ObservationSession(
        id=new_id("obs"),
        source_path=path,
        filename=path.name,
        metadata=metadata,
        scans=scans,
        scan_order=order,
        selected_scan_id=order[0],
        pss_options=pss_options,
    )
    session.add_message("info", f"Loaded {path.name} with {len(scans)} plottable scan series.")
    return session


def _pss_options(hdul: fits.HDUList) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for hdu in hdul:
        if not isinstance(hdu, fits.BinTableHDU) or hdu.data is None:
            continue
        names = _table_names(hdu.data)
        if "PSS_Value" not in names:
            continue
        values = np.asarray(hdu.data["PSS_Value"]).ravel()
        sigmas = np.asarray(hdu.data["PSS_Sigma"]).ravel() if "PSS_Sigma" in names else []
        freqs = np.asarray(hdu.data["PSS_Freq"]).ravel() if "PSS_Freq" in names else []
        sources = np.asarray(hdu.data["PSS_Source"]).ravel() if "PSS_Source" in names else []
        for idx, value in enumerate(values):
            pss = safe_float(value)
            if pss is None:
                continue
            options.append(
                {
                    "value": pss,
                    "sigma": safe_float(sigmas[idx]) if idx < len(sigmas) else None,
                    "frequency": safe_float(freqs[idx]) if idx < len(freqs) else None,
                    "source": str(sources[idx]).strip() if idx < len(sources) else "",
                }
            )
    return options
