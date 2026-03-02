import os,sys

# get the module and class names from the python files
try:
    os.system('rm -rf source/docs')
except:
    pass
os.system('mkdir source/docs')
path=os.path.abspath("../")
print(path)

os.system('sphinx-apidoc -f -o source/docs/ '+path)

# auto build the html and pdf document
os.system("sphinx-build -b html source dran-build")
# os.system("make latexpdf")