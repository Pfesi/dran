
.. dran documentation master file, created by
   sphinx-quickstart on Thu Aug 10 13:15:59 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DRAN's documentation!
================================

Introduction
------------


**DRAN** is a data reduction and analysis software package designed for systematic 
processing of drift scan data collected by `HartRAO's 26m telescope <http://www.hartrao.ac.za/hh26m_factsfile.html>`_. 
It was developed to replace the legacy `LINES <http://www.hartrao.ac.za/hh26m_factsfile.html>`_ software previously 
used at the `Hartebeesthoek Radio Astronomy Observatory <http://www.hartrao.ac.za/>`_. 

The package is implemented in `Python 3.11 <https://www.python.org/downloads/>`_ and provides 
tools for end-to-end drift scan analysis, including:

- Data extraction and preperation,
- Baseline modelling and beam fitting
- Statistical analysis and visualisation

**DRAN**  is intended for both calibrator and target source analysis, with an emphasis on reproducibility, 
automation, and traceability of results.


How DRAN works
--------------

DRAN follows a simple, deterministic workflow.

When a data file is loaded/opened in **DRAN**, observed parameters are extracted and passed through a 
sequence of processing stages:

- Radio frequency interference detection and filtering
- Baseline and drift correction to remove instrumental effects
- Beam fitting using the upper portion of the signal, typically 30 to 50 percent of the :doc:`extras/fitting/peak_fit` region, selected based 
  on signal quality and sidelobe behaviour

Final fit parameters, diagnostics, and derived statistics are written to a database for later analysis. 
All plots generated during processing are saved to a plots directory created in the current working directory.


.. note:: 
   Results are stored in an SQLite database by default. Export to CSV is supported if required.
   **ensure csv conversion is implemented**
   

Interfaces
----------

DRAN supports two primary interfaces:

- :doc:`extras/interface/cli`, intended for automated and batch processing.
- :doc:`extras/interface/gui`, intended for interactive inspection, fitting, 
  and time-series analysis of individual observations.


What to read next
-----------------

To understand the workflow in practice, start with the tutorials in :doc:`extras/tuts/tutorials`.

Installation instructions are provided in :doc:`extras/getting-started/installation`.
A concise overview for first-time users is available in :doc:`extras/getting-started/quickstart`.

Before performing scientific analysis, users are strongly encouraged to review :doc:`extras/caveats`, which outlines 
assumptions, limitations, and known constraints.



Acknowledging DRAN
-------------------

If you use DRAN in a publication, please cite `van Zyl P. 2023 <https://ui.adsabs.harvard.edu/abs/2023arXiv230600764V/abstract>`_.


CONTACTS
---------

If you have any problems, questions, feature requests or suggestions, please 
`OPEN AN ISSUE <https://github.com/Pfesi/dran/issues>`_ **confirm this is the correct path**

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:


   extras/getting-started/installation.rst

   extras/caveats.rst

   extras/getting-started/quickstart.rst

   extras/interface/cli.rst

   extras/interface/gui.rst

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Tutorials:

   extras/tuts/tutorials.rst

   extras/commands.rst

   extras/calibration/calibration.rst

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Resources:

   extras/radio_sources.rst


   .. extras/contributing.rst
   .. extras/code_style.rst
   .. extras/tests.rst
   .. extras/release_notes.rst
   .. extras/code_of_conduct.rst
   .. extras/license.rst

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Guidelines:

   extras/CHANGELOG.rst

   extras/calibration.rst

   extras/common_issues.rst

   docs/modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
