# =========================================================================== #
# File: logging_utils.py                                                      #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import logging
import sys
from pathlib import Path
from typing import Dict
from dran.config.constants import PROJECT_NAME, LOG_FILENAME
# =========================================================================== #


# ANSI escape codes for colored terminal output (supported in most terminals)
RESET: str = "\033[0m"
GREY: str = "\033[90m"
CYAN: str = "\033[36m"
YELLOW: str = "\033[33m"
RED: str = "\033[31m"
RED_BG: str = "\033[41m"


class LevelBasedFormatter(logging.Formatter):
    """
    A logging formatter that applies color-coded and level-specific formats
    for console output.

    Each log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) has its own
    distinct message style to improve readability in terminal output.
    """

    _FORMAT_STRINGS: Dict[int, str] = {
        logging.DEBUG: f"{GREY}DEBUG: %(name)s | %(message)s{RESET}",
        logging.INFO: "%(message)s",
        logging.WARNING: f"{YELLOW}WARNING: %(message)s{RESET}",
        logging.ERROR: f"{RED}ERROR: %(name)s | %(message)s{RESET}",
        logging.CRITICAL: f"{RED_BG}CRITICAL: %(message)s{RESET}"
    }

    def __init__(self) -> None:
        super().__init__()
        self._formatters: Dict[int, logging.Formatter] = {
            level: logging.Formatter(fmt_str, datefmt="%Y-%m-%d %H:%M:%S")
            for level, fmt_str in self._FORMAT_STRINGS.items()
        }
        self._default_formatter = logging.Formatter(
            f"{CYAN}LOG:{RESET} %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record: logging.LogRecord) -> str:
        formatter = self._formatters.get(record.levelno, self._default_formatter)
        return formatter.format(record)


def disclaimer(log: logging.Logger) -> None:
    disclaimer_lines = [
        "Disclaimer: DRAN is a data reduction and analysis software",
        "pipeline developed to systematically reduce and analyze HartRAO's",
        "26m telescope drift-scan data. It comes with no guarantees,",
        "but the author does attempt to assist users to get meaningful results.",
    ]
    for line in disclaimer_lines:
        log.info(line)


def print_start(log: logging.Logger) -> None:
    tab_count: int = 2

    banner_lines = [
        f"{'#' * 11}" * (tab_count * 3),
        "#" + "\t" * (tab_count * 4),
        "#" + "\t" * tab_count + "######  ######  ###### #    #",
        "#" + "\t" * tab_count + "#     # #    #  #    # # #  #",
        "#" + "\t" * tab_count + "#     # #####   ###### #  # #",
        "#" + "\t" * tab_count + "#     # #    #  #    # #   ##",
        "#" + "\t" * tab_count + "######  #    #  #    # #    #",
        "#" + "\t" * (tab_count * 4),
        f"{'#' * 11}" * (tab_count * 3),
    ]

    for line in banner_lines:
        log.info(line)

    disclaimer(log)


def load_prog(prog: str, log: logging.Logger) -> None:
    """
    Print a formatted message indicating the program being loaded.
    Keep this free of OS-specific calls like clearing the console.
    """
    print_start(log)

    separator = "*" * 80
    log.info("")
    log.info(separator)
    log.info("Loading: %s", prog)
    log.info(separator)


def setup_logger(
    debug: bool = False,
    project_name: str =  PROJECT_NAME,
    log_file: str = LOG_FILENAME,
) -> logging.Logger:
    """
    Set up and configure the project logger.
    """
    
    toggle = "on" if debug else "off"
    return configure_logging(project_name, log_file=log_file, toggle=toggle)


def configure_console_logger(logger: logging.Logger, toggle: str = "off") -> None:
    """
    Configure a console handler for the given logger.
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LevelBasedFormatter())

    normalized_toggle = toggle.lower().strip()
    console_level = logging.DEBUG if normalized_toggle == "on" else logging.INFO
    console_handler.setLevel(console_level)

    logger.addHandler(console_handler)


def configure_logging(
    name: str,
    log_file: str | Path,
    toggle: str = "off",
    level: int = logging.DEBUG,
    file_mode: str = "w",
) -> logging.Logger:
    """
    Configure and return a project logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        # Avoid duplicate handlers if configure_logging is called repeatedly.
        for existing_handler in list(logger.handlers):
            logger.removeHandler(existing_handler)
            existing_handler.close()

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode=file_mode, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    configure_console_logger(logger, toggle=toggle)

    logger.debug("Logging initialized.")
    return logger
