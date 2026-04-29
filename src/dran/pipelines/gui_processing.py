# =========================================================================== #
# File: gui_processing.py                                                     #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #


# Standard library imports
# --------------------------------------------------------------------------- #
import argparse
import logging
from pathlib import Path
from typing import Optional
from PyQt5 import QtWidgets
import sys
import os
from dran.utils.fs import ProjectPaths
from dran.gui.main import Main
# =========================================================================== #


def run_gui_processing(
    args: argparse.Namespace,
    paths: ProjectPaths,
    log: logging.Logger) -> None:
    
    # Initialize the Qt application
    app = QtWidgets.QApplication(sys.argv)

    if args.path:
        is_file= os.path.isfile(args.path)
        gui=Main(log,is_file,args.path)
    else:
        gui=Main(log, args.path)
    
    gui.show()
    sys.exit(app.exec())
    
def main():
    app = QtWidgets.QApplication()
    gui=Main()
    gui.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()