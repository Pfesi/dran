import os


# os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/HydraA_13NB')
# os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/Jupiter_24GHz')
# os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/Jupiter_22GHz')
# os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/HydA_35')
os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/HydA_6')
os.system('uv run src/dran/main.py -mode serve --remote-paths calibration/HydA_2.5cmWB')

# os.system('uv run src/dran/main.py -mode serve --remote-paths j1427-4206')
os.system('uv run src/dran/main.py -mode serve --remote-paths pks0454-234')
os.system('uv run src/dran/main.py -mode serve --remote-paths pks1510-089')
os.system('uv run src/dran/main.py -mode serve --remote-paths pks0903-57')
# os.system('uv run src/dran/main.py -mode serve --remote-paths pks2326-502')
os.system('uv run src/dran/main.py -mode serve --remote-paths pks2155-304')
# os.system('uv run src/dran/main.py -mode serve --remote-paths data')