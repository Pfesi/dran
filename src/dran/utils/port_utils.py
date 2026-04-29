# =========================================================================== #
# File: port_utils.py                                                         #                          
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =>========================================================================= #


# Library imports
# --------------------------------------------------------------------------- #
import os
import signal
import subprocess
from typing import List
# =========================================================================== #


def find_pids_by_port(port: int) -> List[int]:
    """
    Find all PIDs using a given port.

    Uses `lsof`, which is available on macOS and most Linux systems.
    """
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )

        if not result.stdout.strip():
            return []

        return [int(pid) for pid in result.stdout.strip().splitlines()]

    except Exception:
        return []


def kill_processes_on_port(port: int, force: bool = False) -> None:
    """
    Kill all processes using a given port.

    Args:
        port: Port number to check
        force: If True, use SIGKILL (-9). Otherwise SIGTERM (default)
    """
    pids = find_pids_by_port(port)

    if not pids:
        print(f"No process found on port {port}")
        return

    for pid in pids:
        try:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            print(f"Killed PID {pid} on port {port} (force={force})")
        except ProcessLookupError:
            print(f"PID {pid} no longer exists")
        except PermissionError:
            print(f"No permission to kill PID {pid}")
            