Radio astronomy basics needed for DRAN
======================================

FITS files
----------

FITS files store astronomy data in Header Data Units, usually called HDUs.
An HDU has a header containing metadata and may have data, such as an image or binary table.
DRAN relies on expected HDU positions and expected header names to extract telescope and observing metadata.

Single-dish drift scans
-----------------------

A drift scan records the telescope response while the source passes through the beam, or while the telescope scans across the source in a controlled way.
For the HartRAO continuum workflow represented here, DRAN expects on-source and half-power scan products in FITS HDUs.

Antenna temperature
-------------------

``T_A`` is antenna temperature.
It measures received power expressed as an equivalent temperature.
DRAN estimates ``T_A`` from fitted scan peaks after cleaning and baseline correction.

Flux density
------------

Flux density is usually reported in jansky.
DRAN's inspected code focuses on extracting and fitting antenna temperature and correction fields.
For calibrated flux-density products, you need a documented flux scale, gain curve, opacity correction, and calibrator model.

Polarization channels
---------------------

The FITS scan tables use ``Count1`` and ``Count2``.
DRAN maps these to LCP and RCP-like data streams and stores them as lower-case data keys before the row fields are normalised.
Fitted output fields use ``L`` and ``R`` polarization letters.

Beam width terms
----------------

``HPBW``
   Half-power beam width.
   It marks the width of the main beam at half of the peak response.

``FNBW``
   First-null beam width.
   It marks the approximate width between the first nulls around the main beam.

``OFFSET``
   The independent scan coordinate generated from ``SCANDIST`` and sample count.

RFI
---

Radio-frequency interference is non-astronomical signal that contaminates the scan.
DRAN uses residual-based rejection and refitting to remove RFI-like outliers.
This is a statistical cleaning method, not a physical proof that a point is interference.

Baseline
--------

A baseline is the slowly varying background or instrumental trend under the source response.
DRAN fits a linear baseline using selected off-source regions, subtracts it, and then fits the source peak.

Pointing correction
-------------------

Pointing errors reduce the measured peak response.
DRAN estimates a correction from the relationship between the on-source scan and half-power scans.
This requires valid fitted peaks for the relevant scan positions.

Radio frequency bands
---------------------

Bands are defined by frequency ranges in MHz:

- L: 1000-1999 MHz
- S: 2000-3999 MHz
- C: 4000-5999 MHz
- CM: 6000-7999 MHz (C-band for maser observations)
- X: 8000-11999 MHz
- KU: 12000-17999 MHz
- K: 18000-25999 MHz