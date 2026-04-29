.. Data extraction and preperation page

Data extraction and reduction
===============================

The data extraction and reduction process converts raw FITS files into 
structured, quality-checked data products. It extracts spectra and 
metadata, applies calibration and quality-control checks, flags bad scans, 
and prepares the observations for modelling, baseline fitting, flux extraction, 
and storage. 

1. `process_fits_path()` - Entry point, walks directory or processes single file

2. `process_observation()` - Extracts metadata from FITS headers

3. `pipeline.py` - Data reduction steps:

   - Baseline correction
   - RFI cleaning
   - Gaussian fitting
   - Atmospheric corrections
   - Calibration to antenna temperature
