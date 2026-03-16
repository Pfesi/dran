# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from pathlib import Path
import sys

project = 'DRAN'
copyright = '2026, pfesesani van zyl'
author = 'pfesesani van zyl'
# release = '0.1.0'

VERSION: str = "0.6.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
print('\n*** Added ROOT path for src files: ', _ROOT,'\n')

extensions = [
    # 'recommonmark', # create .md files
    # Auto-generate section labels.
    'sphinx.ext.autosectionlabel',
    
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx_book_theme',
    
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    
    'sphinx.ext.coverage',
    'myst_parser', # for inline equations
    'sphinx.ext.mathjax',
    
    'sphinx.ext.githubpages',
    'myst_parser',
    'sphinx.ext.duration',
    # 'nbsphinx'
]

myst_enable_extensions = [
    "dollarmath",
    "amsmath",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme" #'sphinx_rtd_theme' ##'alabaster' #pydata-sphinx-theme

html_theme_options = {
  "use_sidenotes": True,
}

html_static_path = ['_static']
# html_css_files = ['css/custom.css'] # relative to _static path
# html_js_files = ['js/custom.js']

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
}

source_parsers = {'.md': 'recommonmark.parser.CommonMarkParser'}

# EPUB options
epub_show_urls = 'footnote'

# def setup(app):
#     app.add_css_file("css/custom.css")