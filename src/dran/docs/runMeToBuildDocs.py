# =========================================================================== #
# File: runMEToBuilsDocs.py                                                   #
# Author: Pfesesani V. van Zyl                                                #
# Email: pfesi24@gmail.com                                                    #
# =========================================================================== #

# Creates the html docs
# ======================
# Library imports
# --------------------------------------------------------------------------- #
import os,sys
from pathlib import Path
# =========================================================================== #


# get root path
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

def main():
    # get the module and class names from the python files
    try:
        os.system(f'rm -rf {_ROOT}/source/docs')
    except:
        pass
    os.system(f'mkdir {_ROOT}/source/docs')
    
    os.system(f'sphinx-apidoc -f -o {_ROOT}/source/docs/ '+str(_ROOT.parent))

    # auto build the html and pdf document
    os.system(f"sphinx-autobuild -b html {_ROOT}/source dran-build")
    # os.system("make latexpdf")

def run_build():
    # get the module and class names from the python files
    try:
        os.system(f'rm -rf {_ROOT}/source/docs')
    except:
        pass
    os.system(f'mkdir {_ROOT}/source/docs')
    os.system(f'sphinx-apidoc -f -o {_ROOT}/source/docs/ '+str(_ROOT.parent))


    # auto build the html and pdf document
    os.system(f"sphinx-build -b html {_ROOT}/source dran-build")
    # os.system("make latexpdf")

if __name__ == "__main__":
    main()
    