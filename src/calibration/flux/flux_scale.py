# flux_scale.py
# Calibrator flux density models (Ott, others later), returns flux for a row.
from __future__ import annotations

from typing import Any, Mapping
import numpy as np


_OTT_1994 = {
    "3C48": {"range_from": 1408, "range_to": 23780, "a": 2.465, "b": -0.004, "c": -0.1251},
    "3C123": {"range_from": 1408, "range_to": 23780, "a": 2.525, "b": 0.246, "c": -0.1638},
    "3C147": {"range_from": 1408, "range_to": 23780, "a": 2.806, "b": -0.140, "c": -0.1031},
    "3C161": {"range_from": 1408, "range_to": 10550, "a": 1.250, "b": 0.726, "c": -0.2286},
    "HYDRAA": {"range_from": 1408, "range_to": 12500, "a": 4.729, "b": -1.025, "c": 0.0130},
    "0915-119": {"range_from": 1408, "range_to": 12500, "a": 4.729, "b": -1.025, "c": 0.0130},
    "0915-11": {"range_from": 1408, "range_to": 12500, "a": 4.729, "b": -1.025, "c": 0.0130},
    "J0918-1205": {"range_from": 1408, "range_to": 12500, "a": 4.729, "b": -1.025, "c": 0.0130},
    "3C227": {"range_from": 1408, "range_to": 4750, "a": 6.757, "b": -2.801, "c": 0.2969},
    "3C249.1": {"range_from": 1408, "range_to": 4750, "a": 2.537, "b": -0.565, "c": -0.0404},
    "VIRGOA": {"range_from": 1408, "range_to": 10550, "a": 4.484, "b": -0.603, "c": -0.0280},
    "3C286": {"range_from": 1408, "range_to": 43200, "a": 0.956, "b": 0.584, "c": -0.1644},
    "3C295": {"range_from": 1408, "range_to": 32000, "a": 1.490, "b": 0.756, "c": -0.2545},
    "3C309.1": {"range_from": 1408, "range_to": 32000, "a": 2.617, "b": -0.437, "c": -0.0373},
    "3C348": {"range_from": 1408, "range_to": 10550, "a": 3.852, "b": -0.361, "c": -0.1053},
    "HERCULESA": {"range_from": 1408, "range_to": 10550, "a": 3.852, "b": -0.361, "c": -0.1053},
    "3C353": {"range_from": 1408, "range_to": 10550, "a": 3.148, "b": -0.157, "c": -0.0911},
    "CYGNUSA": {"range_from": 4750, "range_to": 10550, "a": 8.360, "b": 1.565, "c": 0.0},
    "NGC7027": {"range_from": 10550, "range_to": 43200, "a": 1.322, "b": -0.134, "c": 0.0},
}

_ALIAS = {
    "HYDRA A": "HYDRAA",
    "3C218": "HYDRAA",
    "VIRGO A": "VIRGOA",
    "VIR A": "VIRGOA",
    "3C274": "VIRGOA",
    "HERCULES A": "HERCULESA",
    "CYGNUS A": "CYGNUSA",
    "CYG A": "CYGNUSA",
    "3C405": "CYGNUSA",
}


def calibrator_flux_ott_1994(row: Mapping[str, Any]) -> float:
    obj = str(row.get("OBJECT", "") or "").upper()
    obj = _ALIAS.get(obj, obj)
    centfreq = float(row.get("CENTFREQ", float("nan")))
    logfreq = float(row.get("LOGFREQ", float("nan")))

    if not np.isfinite(centfreq) or not np.isfinite(logfreq):
        return float("nan")

    params = _OTT_1994.get(obj)
    if params is None:
        return float("nan")

    if not (float(params["range_from"]) <= centfreq <= float(params["range_to"])):
        return float("nan")

    a = float(params["a"])
    b = float(params["b"])
    c = float(params["c"])
    return float(10.0 ** (a + b * logfreq + c * (logfreq ** 2)))
