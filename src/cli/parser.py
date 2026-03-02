# =========================================================================== #
# File: parser.py                                                             #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =|========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import argparse
from pathlib import Path
from src.config.constants import VERSION
from src.utils.paths import resolve_existing_path_without_logger
# =|========================================================================= #


def _positive_int(value: str) -> int:
    """
    Parse and validate a positive integer for argparse input.

    Converts the provided string to an integer and ensures the value
    is strictly greater than zero.

    Args:
        value (str): The input string received from the command line.

    Returns:
        int: The validated positive integer.

    Raises:
        argparse.ArgumentTypeError:
            - If the value cannot be converted to an integer.
            - If the parsed integer is less than or equal to zero.

    Notes:
        Designed for use as the `type` argument in argparse.add_argument(),
        enforcing positive integer constraints at parse time.
    """
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Must be an integer.") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """
    Construct and return the DRAN command-line interface parser.

    This parser defines all supported CLI options for running the DRAN
    (Drift-scan Reduction and Analysis) system. It configures processing
    inputs, runtime behavior, operating modes, threading, logging,
    database interaction, and web serving parameters.

    Supported capabilities include:

    - FITS file or directory ingestion via --path
    - Debug logging control
    - Optional persistence of plot/lightcurve data to the database
    - Multiple operating modes:
        auto   : Automatically process data
        gui    : Launch desktop GUI interface
        web    : Launch web interface
        anal   : Run analysis-only mode
        docs   : Generate or serve documentation
        serve  : Start backend service
    - Thread pool configuration
    - Web server port configuration
    - Custom working/results directory
    - Version reporting

    Returns
    -------
    argparse.ArgumentParser
        A fully configured parser ready for argument parsing.
    """
    
    parser = argparse.ArgumentParser(
        prog="DRAN",
        description="Begin processing HartRAO drift-scan data from the Hart 26m telescope.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-path",
        "--path",
        type=Path,
        required=False,
        help="Path to a FITS file or directory containing FITS files.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    
    parser.add_argument(
        "--saveplotstodb",
        action="store_true",
        default=False,
        help="Save plot data / lightcurves in database.",
    )

    parser.add_argument(
        "-mode",
        "--mode",
        choices=["auto", "gui", "web", "anal", "docs", "serve"],
        default="auto",
        help="Operating mode.",
    )

    parser.add_argument(
        "-threads",
        "--threads",
        type=_positive_int,
        default=None,
        help="Number of worker threads.",
    )

    parser.add_argument(
        "-port",
        "--port",
        type=int,
        default=4000,
        help="Port number for web interface.",
    )

    parser.add_argument(
        "-workdir",
        "--workdir",
        type=Path,
        default=Path("DRAN_RESULTS"),
        help="Working/results directory.",
    )

    parser.add_argument(
        "-v",
        action="version",
        version="%(prog)s " + VERSION,
    )

    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    """Normalize parsed command-line arguments.
    Resolves path and workdir to validated existing filesystem paths and 
    returns the updated namespace.
    """
    if isinstance(args.path, Path):
        args.path = resolve_existing_path_without_logger(args.path)

    if isinstance(args.workdir, Path):
        args.workdir = resolve_existing_path_without_logger(args.workdir)
    return args


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """
    Validate command-line arguments and enforce required constraints.

    This function ensures that:
    1. When mode is set to "auto", a path argument is provided.
    2. If a path is supplied, it exists on the filesystem.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    parser : argparse.ArgumentParser
        Argument parser instance used to raise user-friendly CLI errors.

    Raises
    ------
    SystemExit
        Triggered via parser.error() if:
        - mode="auto" and no path is provided.
        - The provided path does not exist.

    Notes
    -----
    - Expands user home shortcuts (e.g. "~") before checking existence.
    - Validation errors terminate execution with a clear CLI message.
    """
    
    if args.mode == "auto" and args.path is None:
        parser.error("Missing required argument: -path/--path (required for mode=auto)")

    if isinstance(args.path, Path):
        path_obj = args.path.expanduser()
        if not path_obj.exists():
            parser.error(f"Path does not exist: {path_obj}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments and return a normalized namespace.
    Builds the argument parser, parses the provided argument list or 
    sys.argv, and applies post-processing to ensure consistent argument values.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    args = normalize_args(args)
    validate_args(args, parser)
    return args
