# =========================================================================== #
# File: models.py                                                             #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
from .plot_qc import ScanQualityResult
from dataclasses import dataclass, field
from typing import Optional, Any
import numpy as np
from numpy.typing import NDArray
# =========================================================================== #


@dataclass(frozen=True)
class ResidualFit:
    """
    Container for Residual fit results.
    """
    rms: float
    residuals: NDArray[np.floating]


@dataclass(slots=True)
class CleanedScan:
    x: np.ndarray
    y: np.ndarray
    rms: float
    residual: np.ndarray
    spline_max: float
    spline: np.ndarray
    points_deleted: np.ndarray
    raw_rms: np.ndarray
    raw_residuals: np.ndarray
    flag: int = 0
    message: str = ""
    
    
@dataclass(slots=True)
class BeamFitResult:
    
    qc: ScanQualityResult = field(default_factory=ScanQualityResult)
    # Peak fit (quadratic over main-beam top fraction)
    peak_coeffs: Optional[np.ndarray] = None
    peak_model: Optional[np.ndarray] = None
    ta_peak: float = float("nan")
    ta_peak_err: float = float("nan")
    peak_loc_index: Optional[int] = None

    # Baseline correction artefacts
    baseline_coeffs: Optional[np.ndarray] = None
    baseline_residual: Optional[np.ndarray] = None
    baseline_rms: float = float("nan")
    baseline_window_indices: Optional[np.ndarray] = None
    y_corrected: Optional[np.ndarray] = None
    y_corrected_spline: Optional[np.ndarray] = None

    # Cleaning artefacts
    clean_rms: float = float("nan")

    # Status
    flag: int = 0
    message: str = ""
    # qc: ScanQualityResult = ScanQualityResult(ok=True,flag=0,message="",metrics={})


@dataclass
class DualBeamQCResult:
    # Defaults represent "QC not computed yet".
    is_bad: bool = True
    flag: int = 0
    reasons: list[str] = field(default_factory=lambda: ["QC not computed"])
    step_max: float = 0.0
    step_count: int = 0
    max_gap_frac: float = 0.0
    snr_a: float = 0.0
    snr_b: float = 0.0
    resid_rms_a: float = 0.0
    resid_rms_b: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "is_bad": getattr(self, "is_bad", None),
            "flag": getattr(self, "flag", None),
            "reasons": getattr(self, "reasons", ""),
            "step_max": getattr(self, "step_max", None),
            "step_count": getattr(self, "step_count", None),
            "max_gap_frac": getattr(self, "metrics", None),
            "snr_a": getattr(self, "snr_a", None),
            "snr_b": getattr(self, "snr_b", None),
            "resid_rms_a": getattr(self, "resid_rms_a", None),
            "resid_rms_b": getattr(self, "resid_rms_b", None),
        }
        
        
@dataclass(slots=True)
class DualBeamFitResult:
    qc: DualBeamQCResult = field(default_factory=DualBeamQCResult)
    # Peak fit (quadratic over main-beam top fraction)
    # apeak_coeffs: Optional[np.ndarray] = None
    # apeak_model: Optional[np.ndarray] = None
    apeak_residuals: float = float("nan")
    ata_peak: float = float("nan")
    ata_peak_err: float = float("nan")
    apeak_loc_index: Optional[int] = None

    # bpeak_coeffs: Optional[np.ndarray] = None
    # bpeak_model: Optional[np.ndarray] = None
    bpeak_residuals: float = float("nan")
    bta_peak: float = float("nan")
    bta_peak_err: float = float("nan")
    bpeak_loc_index: Optional[int] = None

    # Baseline correction artefacts
    baseline_coeffs: Optional[np.ndarray] = None
    baseline_residuals: Optional[np.ndarray] = None
    baseline_rms: float = float("nan")
    baseline_window_indices: Optional[np.ndarray] = None
    y_corrected: Optional[np.ndarray] = None
    y_corrected_spline: Optional[np.ndarray] = None

    # Cleaning artefacts
    clean_rms: float = float("nan")

    # Status
    flag: int = 0
    message: str = ""


@dataclass(slots=True)
class IterativeCleaningResult:
    x: np.ndarray
    y: np.ndarray
    rms: float
    residual: np.ndarray
    spline_max: float
    spline: np.ndarray
    points_deleted: int
    flag: int = 0
    names: Optional[list[Any]] = None
    message: str = ""


def sig_to_noise(ta_peak: float, residual: np.ndarray, log) -> Optional[float]:
    """
    Calculate the signal to noise ratio. i.e. Amplitude / (stdDeviation of noise)
    Taken from paper on 'Signal to Noise Ratio (SNR) Enhancement Comparison of Impulse-, 
    Coding- and Novel Linear-Frequency-Chirp-Based Optical Time Domain Reflectometry 
    (OTDR) for Passive Optical Network (PON) Monitoring Based on Unique Combinations of 
    Wavelength Selective Mirrors'

    Photonics 2014, 1, 33-46; doi:10.3390/photonics1010033
    https://www.mdpi.com/2304-6732/1/1/33
    https://www.mdpi.com/68484

    Args:
        signalPeak (float) : The maximum valueof a desired signal
        noise (array): array of fit residuals
        log(object): file logging object
        
    Returns:
        sig2noise (float): signal to noise ratio

    Returns SNR, or None if it cannot be computed.
    """
    
    ta_peak=abs(ta_peak)
    if residual is None or len(residual) == 0:
        log.warning("SNR skipped. residual is empty.")
        return None

    rms = float(np.sqrt(np.nanmean(np.asarray(residual, dtype=float) ** 2)))

    if not np.isfinite(rms) or rms <= 0.0:
        log.warning("SNR skipped. Invalid rms=%s", rms)
        return None

    if not np.isfinite(ta_peak):
        log.warning("SNR skipped. Invalid ta_peak=%s", ta_peak)
        return None

    return float(ta_peak / rms)
