Tutorials
=========


DRAN follows this practical flow:

1. Read one FITS file or walk a directory of FITS files.
2. Validate paths and skip known invalid, duplicate, empty, or broken-symlink files.
3. Extract FITS headers from known HDU positions.
4. Extract drift-scan arrays from known scan HDUs.
5. Convert detector counts to Kelvin when noise-diode conversion factors are available.
6. Derive weather and atmospheric fields from metadata.
7. Fit single-beam or dual-beam drift scans.
8. Apply pointing corrections where the required half-power scans exist.
9. Store rows in a SQLite database, usually one table per source-frequency pair.
10. Save plots under ``PLOTS/<SOURCE>/<FREQUENCY>/``.


These tutorials use the FITS files included with the package under ``src/dran/data``.
The sample tree contains observations for a calibrator source ``HydraA`` and 
a target source ``J1427-4206`` at frequencies 2280 MHz, 4800 MHz, 8280 MHz
and 12218 MHz.


Tutorial
--------

1. :doc:`tut_sband`

2. :doc:`tut_xband`

3. :doc:`Calibration of Hydra A at s-band <2GHz_HydraA_tutorial>`
