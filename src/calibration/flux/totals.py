# totals.py
# Total flux combining channels.
# from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True, slots=True)
class TotalFluxResult:
    total: float
    total_err: float
    n: int
    sum_flux: float


def total_flux_4chan(
    a_l: float, a_l_err: float,
    a_r: float, a_r_err: float,
    b_l: float, b_l_err: float,
    b_r: float, b_r_err: float,
) -> TotalFluxResult:
    f = np.array([a_l, a_r, b_l, b_r], dtype=float)
    e = np.array([a_l_err, a_r_err, b_l_err, b_r_err], dtype=float)

    f = np.abs(f)
    e = np.abs(e)

    valid = np.isfinite(f) & (f > 0.0)

    n = int(valid.sum())
    if n == 0:
        return TotalFluxResult(float("nan"), float("nan"), 0, 0.0)

    sum_flux = float(np.where(valid, f, 0.0).sum())
    var = float(np.where(np.isfinite(e), e * e, 0.0).sum())
    sum_err = float(np.sqrt(var))

    total = (sum_flux / n) * 2.0
    total_err = (2.0 / n) * sum_err

    return TotalFluxResult(float(total), float(total_err), n, sum_flux)
