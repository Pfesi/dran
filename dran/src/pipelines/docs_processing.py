# =========================================================================== #
# File: docs_processing.py                                                    #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Standard library imports
# --------------------------------------------------------------------------- #
import webbrowser
import logging
import subprocess
import sys
from pathlib import Path
# =========================================================================== #


def run_docs_processing(args, paths, log: logging.Logger) -> None:
   
    """ 
    Open the source documentation.
    """
    
    docs_dir = Path(__file__).resolve().parents[1] / "docs" / "dran-build"
    index_file = docs_dir / "index.html"
    port = args.port
    
    log.debug("Serving docs from directory: %s", docs_dir)
    log.debug("Opening docs file: %s", index_file)
    log.debug("Port: %s", port)

    if not docs_dir.exists():
        raise RuntimeError(f"Docs directory does not exist: {docs_dir}")

    if not docs_dir.is_dir():
        raise RuntimeError(f"Docs path is not a directory: {docs_dir}")

    if not index_file.exists():
        raise RuntimeError(f"Docs index file does not exist: {index_file}")

    try:
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=str(docs_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        url = f"http://127.0.0.1:{port}/index.html"
        webbrowser.open_new_tab(url)
        log.info("Browser opened at %s", url)

    except Exception as exc:
        log.error("Failed to launch docs server: %s", exc)
        raise RuntimeError("Docs server launch failed.") from exc
    