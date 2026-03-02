# =========================================================================== #
# File: ta_corrections.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# ---------------------------------------------------------------------------- #
from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np
# =|========================================================================= #


@dataclass(frozen=True, slots=True)
class TaCorrectionResult:
    corrected_ta: float
    corrected_ta_err: float
    ok: bool
    reason: str


def apply_ta_corrections(
    on_ta: float,
    on_err: float,
    pc: float,
    pc_err: float,
    row: Mapping[str, Any],
) -> TaCorrectionResult:
    """
    Apply pointing gain factor and any frontend-specific corrections.

    Notes
    - pc is a multiplicative gain correction factor.
    - This preserves your existing behavior for Jupiter at 01.3S.
    """

    on_ta = float(on_ta) if on_ta is not None else float("nan")
    on_err = float(abs(on_err)) if on_err is not None else float("nan")

    if not np.isfinite(on_ta) or on_ta == 0.0:
        return TaCorrectionResult(float("nan"), float("nan"), False, "invalid on_ta")

    if not np.isfinite(pc) or pc <= 0.0:
        return TaCorrectionResult(float("nan"), float("nan"), False, "invalid pc")

    frontend = str(row.get("FRONTEND", "") or "")
    obj = str(row.get("OBJECT", "") or "").upper()

    mult = pc
    mult_var = (pc_err / pc) ** 2 if np.isfinite(pc_err) and pc != 0.0 else float("nan")

    if frontend == "01.3S" and obj == "JUPITER":
        abs_corr = float(row.get("ATMOS_ABSORPTION_CORR", float("nan")))
        scf = float(row.get("SIZE_CORRECTION_FACTOR", float("nan")))

        if np.isfinite(abs_corr) and abs_corr > 0.0:
            mult *= abs_corr
            mult_var = mult_var if np.isfinite(mult_var) else 0.0
        else:
            return TaCorrectionResult(float("nan"), float("nan"), False, "invalid ATMOS_ABSORPTION_CORR")

        if np.isfinite(scf) and scf > 0.0:
            mult *= scf
            mult_var = mult_var if np.isfinite(mult_var) else 0.0
        else:
            return TaCorrectionResult(float("nan"), float("nan"), False, "invalid SIZE_CORRECTION_FACTOR")

    corrected = on_ta * mult

    # Error propagation for corrected Ta:
    # corr = on_ta * mult
    # var = (on_err * mult)^2 + (on_ta * mult * rel_mult_err)^2
    rel_mult_err = float(np.sqrt(mult_var)) if np.isfinite(mult_var) else float("nan")

    if np.isfinite(rel_mult_err):
        var = (on_err * mult) ** 2 + (on_ta * mult * rel_mult_err) ** 2
        corrected_err = float(np.sqrt(var))
        ok = np.isfinite(corrected_err)
        reason = "ok" if ok else "non-finite corrected_err"
    else:
        corrected_err = float("nan")
        ok = False
        reason = "mult uncertainty unavailable"

    return TaCorrectionResult(corrected, corrected_err, ok, reason)
