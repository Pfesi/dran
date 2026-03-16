# =========================================================================== #
# File: constants.py                                                          #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
from datetime import datetime
from typing import Final
import math
from typing import Dict, Tuple
# =|========================================================================= #


# App configuration
PROJECT_NAME: Final[str] = "DRAN"
VERSION: str = "0.7.0"
RELEASE: str = "1.0"
YEAR: str = str(datetime.now().year)

AUTHOR: Final[str] = "Pfesesani V. van Zyl"
EMAIL: Final[str] = "pfesi24@gmail.com"
COPYRIGHT: Final[str] = f"{YEAR}, {AUTHOR}"


# Logging configuration
BORDER: Final[str] = "*" * 80


# Database configuration
DB_NAME: Final[str] = "HART26DATA.db"


# Output directory names (names only, not Paths)
DIAGNOSTICS_DIRNAME: Final[str] = "DIAGNOSTIC_PLOTS"
PLOTS_DIRNAME: Final[str] = "PLOTS"


# Output file names (names only, not Paths)
LOG_FILENAME: Final[str] = "LOGGING.txt"
INVALID_FILES_FILENAME: Final[str] = "CORRUPT_FILE_PATHS.txt"
SYMLINKS_FILENAME: Final[str] = "SYMLINK_PATHS.txt"


# FITS FILE KEYS
PR_KEYS: Final[list[str]] = [
    "DATE",
    "OBJECT",
    "LONGITUD",
    "LATITUDE",
    "EQUINOX",
    "OBSERVER",
    "OBSLOCAL",
    "PROJNAME",
    "PROPOSAL",
    "TELESCOP",
    "UPGRADE",
    "FOCUS",
    "TILT",
    "TAMBIENT",
    "PRESSURE",
    "HUMIDITY",
    "WINDSPD",
    "SCANTYPE",
    "INSTRUME",
    "STEPSEQ",
    "SCANDIST",
    "SCANANGL",
    "SCANTIME",
    "SCANDIR",
    "POINTING",
]

FS_KEYS: Final[list[str]] = [
    "EXTNAME",
    "FEEDTYPE",
    "BMOFFHA",
    "BMOFFDEC",
    "HPBW",
    "FNBW",
    "SNBW",
    "NOMTSYS",
    "DICHROIC",
    "PHASECAL",
]

ND_KEYS: Final[list[str]] = [
    "FRONTEND",
    "CENTFREQ",
    "BANDWDTH",
    "TCAL1",
    "TCALSIG1",
    "TCAL2",
    "TCALSIG2",
    "SCANTIME",
]

C_KEYS: Final[list[str]] = [
    "TSYS1",
    "TSYSERR1",
    "TSYS2",
    "TSYSERR2",
]


# Results columns
COMM: Final[list[str]] = [
    "MJD",
    "LOGFREQ",
    "HOUR_ANGLE",
    "ZA",
    "ELEVATION",
    "AZIMUTH",
    "DECLINATION",
    "RA_APPARENT",
    "DEC_APPARENT",
    "RA_MEAN",
    "DEC_MEAN",
    "RA_B1950",
    "DEC_B1950",
    "RA_J2000",
    "DEC_J2000",
    "GALACTIC_LONG",
    "GALACTIC_LAT",
    "ECLIPTIC_LONG",
    "ECLIPTIC_LAT",
    "USER_LONG",
    "USER_LAT",
    "HA_ERROR",
    "DEC_ERROR",
]

COMM_WEATHER: Final[list[str]] = [
    "PWV", "SVP", "AVP", "DPT", "WVD", 
    "HUMIDITY", "TAMBIENT"]

WB_WEATHER: Final[list[str]] = ["ATMOSABS"]

NB_WEATHER_KU: Final[list[str]] = [
    "MEAN_ATMOS_CORRECTION",
    "TAU10",
    "TAU15",
    "TBATMOS10",
    "TBATMOS15",
]

NB_WEATHER_K: Final[list[str]] = [
    "TAU221", "TAU2223", "TBATMOS221", "TBATMOS2223"]

JUP_WEATHER: Final[list[str]] = [
    "HPBW_ARCSEC",
    "ADOPTED_PLANET_TB",
    "SYNCH_FLUX_DENSITY",
    "PLANET_ANG_EQ_RAD",
    "PLANET_SOLID_ANG",
    "PLANET_ANG_DIAM",
    "JUPITER_DIST_AU",
    "SIZE_FACTOR_IN_BEAM",
    "SIZE_CORRECTION_FACTOR",
    "MEASURED_TCAL1",
    "MEASURED_TCAL2",
    "MEAS_TCAL1_CORR_FACTOR",
    "MEAS_TCAL2_CORR_FACTOR",
    "ZA_RAD",
    "THERMAL_PLANET_FLUX_D",
    "TOTAL_PLANET_FLUX_D",
    "TOTAL_PLANET_FLUX_D_WMAP",
    "ATMOS_ABSORPTION_CORR",
]

DB_WEATHER: Final[list[str]] = [
    "SEC_Z",
    "X_Z",
    "DRY_ATMOS_TRANSMISSION",
    "ZENITH_TAU_AT_1400M",
    "ABSORPTION_AT_ZENITH",
]


# Weather columns by band
# Values are lists of column lists. Shape: dict[str, list[list[str]]]
WEATHER_BY_BAND: Final[dict[str, list[list[str]]]] = {
    "L": [WB_WEATHER],
    "S": [WB_WEATHER],
    "C": [DB_WEATHER],
    "X": [DB_WEATHER],
    "CM": [WB_WEATHER],
    "KU": [NB_WEATHER_KU],
    "K": [NB_WEATHER_K],
}

LABEL_KWARGS_BY_BAND: Final[dict[str, dict[str, tuple[str, ...]]]] = {
    "C": {"pos": ("N", "S", "O"), "beam": ("A", "B")},
    "X": {"pos": ("N", "S", "O"), "beam": ("A", "B")},
    "CM": {"pos": ("N", "S", "O")},
    "KU": {"pos": ("N", "S", "O")},
    "K": {"pos": ("N", "S", "O")},
}


# Jupiter 22 GHz constants
DEG_TO_RAD: Final[float] = math.pi / 180.0
RAD_TO_DEG: Final[float] = 180.0 / math.pi
ARCSEC_TO_RAD: Final[float] = math.pi / (180.0 * 3600.0)

AU_TO_KM: Final[float]  = 149597870700/1e3 # 1 au = 149597870700  # 1 AU in km (https://ssd.jpl.nasa.gov/astro_par.html)
JUPITER_MEAN_DIAMETER_KM: Final[float]  = 69911 * 2  # Mean diameter in km # from nasa jpl horizons ephemeris data, i.e. mean radius times 2, Last Updated 24/04/2024 


# Fitting configuration
MAX_POINTS: Final[int] = 50

# Centralised band definition to avoid duplication
# Satellite band ranges (MHz) — based on ESA documentation
# https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Satellite_frequency_bands
FREQUENCY_BANDS_MHZ: Dict[str, Tuple[int, int]] = {
    "L": (1000, 1999),
    "S": (2000, 3999),
    "C": (4000, 5999),
    "CM": (6000, 7999),   # C-band maser observations
    "X": (8000, 11999),
    "KU": (12000, 17999),
    "K": (18000, 25999),
    "KA": (26000, 39999),
}

# Band aliases for user input and legacy values.
BAND_ALIASES: Dict[str, str] = {
    "Ku": "KU",
    "Ka": "KA",
    "ku": "KU",
    "ka": "KA",
}

FREQ_ALIASES:Dict[str, str] = {
    "35": "8280",
}