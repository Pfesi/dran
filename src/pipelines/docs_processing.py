# =========================================================================== #
# File: docs.py                                                               #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Standard library imports
# --------------------------------------------------------------------------- #
import webbrowser
import logging
from pathlib import Path
# =========================================================================== #


def run_docs_processing(args, paths, log: logging.Logger) -> None:
   
    """ 
    Open the source documentation.
    """
    
    docs_path = Path(__file__).resolve().parents[1] / "docs" / "dran-build" / "index.html"
    log.info("Opening docs: %s", docs_path)

    try:
        webbrowser.open_new_tab(docs_path.as_uri())
        log.info("Browser opened.")
    except Exception as exc:
        log.error("Failed to open docs in browser: %s", exc)
        raise RuntimeError("Browser launch failed. See logs for details.") from exc
