# obs/__init__.py
"""
Observation ingestion and scan-derivation utilities.

This package is split by responsibility:
- records: output record shaping
- conversions: unit and calibration conversions
- fits_tables: FITS table column extraction helpers
- scan_derived: domain-specific derived fields for scans
- time_axis: time conversion and time axis helpers
- validation: header keyword validation helpers
"""

# from .records import build_observation_record
# from .conversions import counts_to_kelvin
# from .scan_derived import add_scan_arrays_to_record

# __all__ = [
#     "build_observation_record",
#     "counts_to_kelvin",
#     "add_scan_arrays_to_record",
# ]
