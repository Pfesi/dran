import os


os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/HydraA_13NB')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/Jupiter_24GHz')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/Jupiter_22GHz')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/HydA_35')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/HydA_6')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/calibration/HydA_2.5cmWB')

os.system('uv run src/dran/main.py -mode serve --remote-paths data/j1427-4206')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/pks0454-234')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/pks1510-089')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/pks0903-57')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/pks2326-502')
os.system('uv run src/dran/main.py -mode serve --remote-paths data/pks2155-304')
# os.system('uv run src/dran/main.py -mode serve --remote-paths data')