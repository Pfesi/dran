# =========================================================================== #
# File: constants.py                                                          #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #

from datetime import datetime
from typing import Final
import math
import re


# App configuration
PROJECT_NAME: Final = "DRAN"

VERSION: str = "0.9.0"

RELEASE: Final = "1.0"
YEAR: Final = str(datetime.now().year)

AUTHOR: Final = "Pfesesani V. van Zyl"
EMAIL: Final = "pfesi24@gmail.com"
COPYRIGHT: Final = f"{YEAR}, {AUTHOR}"

# Logging
BORDER: Final = "*" * 80

# Database
DB_NAME: Final = "HART26DATA.db"

# Output directories
DIAGNOSTICS_DIRNAME: Final = "DIAGNOSTIC_PLOTS"
PLOTS_DIRNAME: Final = "PLOTS"

# Output files
LOG_FILENAME: Final = "LOGGING.txt"
INVALID_FILES_FILENAME: Final = "CORRUPT_FILE_PATHS.txt"
SYMLINKS_FILENAME: Final = "SYMLINK_PATHS.txt"

# FITS header keys by HDU type
# Primary header
PR_KEYS: Final[tuple[str, ...]] = (
    "DATE", "OBJECT", "LONGITUD", "LATITUDE", "EQUINOX", "OBSERVER",
    "OBSLOCAL", "PROJNAME", "PROPOSAL", "TELESCOP", "UPGRADE", "FOCUS",
    "TILT", "TAMBIENT", "PRESSURE", "HUMIDITY", "WINDSPD", "SCANTYPE",
    "INSTRUME", "STEPSEQ", "SCANDIST", "SCANANGL", "SCANTIME", "SCANDIR",
    "POINTING",
)

# Feed system header
FS_KEYS: Final[tuple[str, ...]] = (
    "EXTNAME", "FEEDTYPE", "BMOFFHA", "BMOFFDEC", "HPBW", "FNBW", "SNBW",
    "NOMTSYS", "DICHROIC", "PHASECAL",
)

# Noise diode header
ND_KEYS: Final[tuple[str, ...]] = (
    "FRONTEND", "CENTFREQ", "BANDWDTH", "TCAL1", "TCALSIG1", "TCAL2",
    "TCALSIG2", "SCANTIME",
)

# Calibration header
C_KEYS: Final[tuple[str, ...]] = ("TSYS1", "TSYSERR1", "TSYS2", "TSYSERR2")

# Results columns
# -----------------
# Common for all obs.
COMM: Final[tuple[str, ...]] = (
    "MJD", "LOGFREQ", "HOUR_ANGLE", "ZA", "ELEVATION", "AZIMUTH",
    "DECLINATION", "RA_APPARENT", "DEC_APPARENT", "RA_MEAN", "DEC_MEAN",
    "RA_B1950", "DEC_B1950", "RA_J2000", "DEC_J2000", "GALACTIC_LONG",
    "GALACTIC_LAT", "ECLIPTIC_LONG", "ECLIPTIC_LAT", "USER_LONG", "USER_LAT",
    "HA_ERROR", "DEC_ERROR",
)

# common weather for all obs.
COMM_WEATHER: Final[tuple[str, ...]] = (
    "PWV", "SVP", "AVP", "DPT", "WVD", "HUMIDITY", "TAMBIENT"
)

# weather for L/S band
WB_WEATHER: Final[tuple[str, ...]] = ("ATMOSABS",)

# weather for Ku/CM band
NB_WEATHER_KU: Final[tuple[str, ...]] = (
    "MEAN_ATMOS_CORRECTION", "TAU10", "TAU15", "TBATMOS10", "TBATMOS15"
)

# weather for K band
NB_WEATHER_K: Final[tuple[str, ...]] = (
    "TAU221", "TAU2223", "TBATMOS221", "TBATMOS2223"
)

# weather for planet jupiter
JUP_WEATHER: Final[tuple[str, ...]] = (
    "HPBW_ARCSEC", "ADOPTED_PLANET_TB", "SYNCH_FLUX_DENSITY",
    "PLANET_ANG_EQ_RAD", "PLANET_SOLID_ANG", "PLANET_ANG_DIAM",
    "JUPITER_DIST_AU", "SIZE_FACTOR_IN_BEAM", "SIZE_CORRECTION_FACTOR",
    "MEASURED_TCAL1", "MEASURED_TCAL2", "MEAS_TCAL1_CORR_FACTOR",
    "MEAS_TCAL2_CORR_FACTOR", "ZA_RAD", "THERMAL_PLANET_FLUX_D",
    "TOTAL_PLANET_FLUX_D", "TOTAL_PLANET_FLUX_D_WMAP", "ATMOS_ABSORPTION_CORR",
)

# weather for C/X band
DB_WEATHER: Final[tuple[str, ...]] = (
    "SEC_Z", "X_Z", "DRY_ATMOS_TRANSMISSION", "ZENITH_TAU_AT_1400M",
    "ABSORPTION_AT_ZENITH",
)

# Weather columns by band: dict[str, tuple[tuple[str, ...], ...]]
WEATHER_BY_BAND: Final = {
    "L": (WB_WEATHER,),
    "S": (WB_WEATHER,),
    "C": (DB_WEATHER,),
    "X": (DB_WEATHER,),
    "CM": (WB_WEATHER,),
    "KU": (NB_WEATHER_KU,),
    "K": (NB_WEATHER_K,),
}

LABEL_KWARGS_BY_BAND: Final = {
    "C": {"pos": ("N", "S", "O"), "beam": ("A", "B")},
    "X": {"pos": ("N", "S", "O"), "beam": ("A", "B")},
    "CM": {"pos": ("N", "S", "O")},
    "KU": {"pos": ("N", "S", "O")},
    "K": {"pos": ("N", "S", "O")},
}

# Unit conversions
DEG_TO_RAD: Final = math.pi / 180.0
RAD_TO_DEG: Final = 180.0 / math.pi
ARCSEC_TO_RAD: Final = math.pi / (180.0 * 3600.0) # 1 arcsecond = 4.84814e-6 rad

AU_TO_KM: Final[float]  = 149597870700/1e3 # 1 au = 149597870700  # 1 AU in km (https://ssd.jpl.nasa.gov/astro_par.html)
JUPITER_MEAN_DIAMETER_KM: Final = 69911 * 2  # NASA JPL Horizons (2024-04-24)
# Mean diameter in km 
# from nasa jpl horizons ephemeris data, i.e. mean radius times 2, Last Updated 24/04/2024 

#  NASA JPL Horizons provides the mean radius (69,911 km),  
#  which is appropriate for radio astronomy flux calculations because:                          
                                                                                               
#   1. Resolved sources: At HartRAO's resolution, Jupiter is often partially resolved, 
#   so the mean diameter better represents the effective emitting area                                  
#   2. Disk-averaged temperature: The brightness temperature calculations use the mean 
# disk area, not equatorial                                                                              
#   3. Ephemeris consistency: Using Horizons values ensures consistency with the
#   distance/position data you're also pulling from there    
  
# Fitting
MAX_POINTS: Final = 50

# Frequency bands (MHz): https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Satellite_frequency_bands
FREQUENCY_BANDS_MHZ: Final = {
    "L": (1000, 1999),
    "S": (2000, 3999),
    "C": (4000, 5999),
    "CM": (6000, 7999),  # C-band maser
    "X": (8000, 11999),
    "KU": (12000, 17999),
    "K": (18000, 25999),
    "KA": (26000, 39999),
}

# Band aliases for user input and legacy values.
BAND_ALIASES: Final = {"Ku": "KU", "Ka": "KA", "ku": "KU", "ka": "KA"}

# Frequency aliases for user input and legacy values.
FREQ_ALIASES: Final = {
    "6": "4800",
    "13": "2270",
    "35": "8280",
    "3.5": "8280",
    "18": "1720",
    "2.5": "12218",
    "21.5": "22000", # DR files have 21.5GHz obs
    "22235": "22275", # DR files
    "23694": "23734",
    "22 cm": "22040",
    "22": "22275",
    "24": "24040",
    "1.3": "22040",
}


_WAVELENGTH_BEAM_RE = re.compile(
    r"^(?P<wavelength>\d+(?:\.\d+)?)(?:cm)?(?P<beam>[A-Za-z]+)$",
    flags=re.IGNORECASE,
)

_WAVELENGTH_ONLY_RE = re.compile(
    r"^(?P<wavelength>\d+(?:\.\d+)?)(?:cm)?$",
    flags=re.IGNORECASE,
)