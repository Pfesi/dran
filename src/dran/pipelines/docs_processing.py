import logging
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

from dran.utils.port_utils import kill_processes_on_port


def run_docs_processing(args, paths, log: logging.Logger) -> None:
    """
    Serve the packaged built docs and open them in a browser.
    """

    try:
        docs_dir = files("dran").joinpath("docs", "dran-build")
        docs_dir = Path(str(docs_dir))
    except Exception as exc:
        raise RuntimeError("Could not locate packaged docs directory.") from exc

    index_file = docs_dir / "index.html"
    port = args.port

    kill_processes_on_port(port, force=True)

    log.debug("Serving docs from directory: %s", docs_dir)
    log.debug("Docs index file: %s", index_file)
    log.debug("Port: %s", port)

    if not docs_dir.exists():
        raise RuntimeError(f"Docs directory does not exist: {docs_dir}")

    if not docs_dir.is_dir():
        raise RuntimeError(f"Docs path is not a directory: {docs_dir}")

    if not index_file.exists():
        raise RuntimeError(f"Docs index file does not exist: {index_file}")

    try:
        handler = partial(SimpleHTTPRequestHandler, directory=str(docs_dir))
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)

        url = f"http://127.0.0.1:{port}/"

        def open_browser() -> None:
            time.sleep(0.5)
            webbrowser.open_new_tab(url)
            log.info("Browser opened at %s", url)

        threading.Thread(target=open_browser, daemon=True).start()

        log.info("Serving docs at %s", url)
        server.serve_forever()

    except KeyboardInterrupt:
        log.info("Docs server stopped by user.")
    except Exception as exc:
        log.error("Failed to launch docs server: %s", exc)
        raise RuntimeError("Docs server launch failed.") from exc