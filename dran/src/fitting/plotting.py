# =========================================================================== #
# File: plotting.py.                                                          #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Library imports
# --------------------------------------------------------------------------- #
import os
from pathlib import Path
from typing import Any, Sequence
import matplotlib.pyplot as plt
from src.utils.paths import parse_plot_path
from src.config.paths import ProjectPaths
from src.utils.time_utils import parse_doy_timestamp
import numpy as np
import logging
# =========================================================================== #


def plot_diagnostics(
    plots: Sequence[Any],
    paths:ProjectPaths,
    log: logging.Logger,
    save_path: str = "",
    plot_type: str = "diagnostic",
    suffix: str = "",
    
) -> None:
    """
    plots: sequence of dicts with keys: x, y, lab, fmt
    Optional keys per dict: axlinet, axlineb
    """
    if not plots:
        log.warning("plot_diagnostics got empty plots input.")
        return

    src_name, freq, fl = ("", "", "")
    if save_path:
        try:
            src_name, freq, fl = parse_plot_path(save_path)
        except Exception:
            pass

    if plot_type == "diagnostic" and save_path:
        base = paths.diagnostics_dir / os.path.basename(save_path)
        derived = base if base.suffix else base.with_suffix(".png")
        out = derived.with_name(derived.stem + suffix)
    else:
        out = Path(save_path) if save_path else None

    fig, ax = plt.subplots()
    if fl and len(fl) >= 18:
        date = parse_doy_timestamp(fl[:18])
        ax.set_title(f"{date} SAST", fontsize=10)
    else:
        ax.set_title("SAST", fontsize=10)
    if src_name and freq and fl:
        fig.suptitle(f"Plot of {src_name} at {freq} MHz")
    else:
        fig.suptitle("Diagnostics")

    if not plots or len(plots) < 1:
        log.warning("test_plot called with insufficient data pairs.")
        return
    
    if plot_type=="fail":
        log.debug('Plot fit failed')
        for spec in plots:
            x = spec["x"]
            y = spec["y"]
            lab = spec["lab"]
            fmt = spec["fmt"]
            ax.plot(x, y, fmt, alpha=0.8, label=lab)

            if "axlinet" in spec:
                ax.axhline(spec["axlinet"], alpha=0.3, color="r")
            if "axlineb" in spec:
                ax.axhline(spec["axlineb"], alpha=0.3, color="r")
        
    else:
        
        for spec in plots:
            x = spec["x"]
            y = spec["y"]
            lab = spec["lab"]
            fmt = spec["fmt"]
            ax.plot(x, y, fmt, alpha=0.8, label=lab)

            if "axlinet" in spec:
                ax.axhline(spec["axlinet"], alpha=0.3, color="r")
            if "axlineb" in spec:
                ax.axhline(spec["axlineb"], alpha=0.3, color="r")

    ax.axhline(0, alpha=0.3, color="k",ls='--')
    ax.set_xlabel("SCANDIST [DEG]")
    ax.set_ylabel("T$_A$ [K]")
    ax.legend(loc="best", fontsize=7)
    
    if out is not None and str(out):
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out, bbox_inches="tight", dpi=150)
            log.debug("Saved plot to %s", out)
        except Exception as exc:
            log.error("Failed saving plot %s. error=%s", out, exc, exc_info=True)

    plt.close(fig)

def plot_fail(
    x: np.ndarray,
    y: np.ndarray,
    paths:ProjectPaths,
    message: str,
    log: logging.Logger,
    save_path: str,
    flag: int,
    fmt: str = "r",
) -> None:
    """
    Plot a single series to document a failure and save it.

    This reproduces your old behavior, but without returning a long tuple.
    """
    plots = [{"x": x, "y": y, "lab": message, "fmt": fmt}]
    plot_diagnostics(plots, paths,log, save_path, plot_type="fail", suffix=".png")
    log.error("Fit failed. flag=%s message=%s", flag, message)
