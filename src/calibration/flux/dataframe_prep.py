# dataframe_prep.py
# Date parsing, numeric coercions, error column cleaning.
from __future__ import annotations

from typing import Iterable
import numpy as np
import pandas as pd


def parse_obsdate_column(df: pd.DataFrame, col: str = "OBSDATE") -> pd.DataFrame:
    out = df.copy()
    s = out[col].astype(str)

    date_str = s.str.split("T").str[0].str.split(" ").str[0]
    out[col] = pd.to_datetime(date_str, errors="coerce").dt.floor("D")

    return out


def make_positive_or_nan(x) -> float:
    if x is None or x == "":
        return float("nan")
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    if not np.isfinite(v):
        return float("nan")
    return float(abs(v))


def ensure_positive_error_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    err_cols = [c for c in out.columns if "ERR" in c]
    for c in err_cols:
        out[c] = out[c].map(make_positive_or_nan)
    return out


def convert_to_numeric_excluding(df: pd.DataFrame, exclude_keywords: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    cols = list(out.columns)
    numeric_cols = [c for c in cols if not any(k in c for k in exclude_keywords)]
    out[numeric_cols] = out[numeric_cols].apply(pd.to_numeric, errors="coerce")
    return out
