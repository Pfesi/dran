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
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Must be an integer.") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.
    Defines all supported CLI options, defaults, and validation rules for 
    running DRAN in different operating modes.
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
