DRAN documentation
================================

Introduction
------------

``DRAN`` is a data reduction and 
analysis python package developed for the systematic processing of 
single-dish drift scan data from `HartRAO's 26m telescope <http://www.hartrao.ac.za/hh26m_factsfile.html>`_. 
It was developed to replace the legacy ``LINES`` software previously 
used at the `Hartebeesthoek Radio Astronomy Observatory <http://www.hartrao.ac.za/>`_. 

The package is implemented in `Python 3.11 <https://www.python.org/downloads/>`_ and provides 
tools for simple data processing, including:

- Data extraction and reduction
- Modelling an beam fitting
- Statistical analysis and visualization
  
.. - :doc:`api/reduction/data_extraction_and_prep`
.. - :doc:`api/fitting/model_and_fit`
.. - :doc:`api/vis/stat_anal_and_vis`


.. Final fit parameters, diagnostics, and derived statistics are written to an 
.. `SQLITE <https://sqlite.org>`_ database for later analysis. All plots generated 
.. during processing are saved to the ``PLOTS`` directory created in the ``current 
.. working directory``.



.. Interfaces
.. ----------
DRAN uses a :doc:`api/interface/cli` driven workflow in which the 
user runs processing, analysis, inspection, and reporting tasks 
through terminal commands, allowing the data reduction process to 
remain reproducible, scriptable, and easier to automate.

For closer inspection of individual observations, DRAN also 
provides a :doc:`api/interface/gui` for fitting, visual 
inspection, and time-series analysis. 

A :doc:`api/interface/web` is 
currently in development and is intended to provide browser-based 
access to selected DRAN tools.

.. DRAN supports 3 primary interfaces:

.. - :doc:`api/interface/cli`, intended for automated and batch processing.
.. - :doc:`api/interface/gui`, intended for interactive inspection, fitting, 
..   and time-series analysis of individual observations.
.. - :doc:`api/interface/web`, currently in development.


.. Ports
.. -----

.. To run this documentation interface, the port defaults to port 4000. This can be 
.. changed using 

.. .. info:: bash
..    dran --mode docs --port new_port_number


.. .. warning::
..    The new_port_number should be an integer.


Getting started
---------------

- For instructions in installing ``DRAN`` see the :doc:`installation` page.

- For a short introduction to using ``DRAN`` see the :doc:`quickstart`.

- For more detailed examples, refer to the :doc:`tuts/index`.


Before performing scientific analysis, users are strongly 
encouraged to review :doc:`caveats`, which outlines assumptions, 
limitations, and known constraints.



Acknowledging DRAN
-------------------

If you use DRAN in a publication, please cite `van Zyl P. 2023 <https://ui.adsabs.harvard.edu/abs/2023arXiv230600764V/abstract>`_.


Getting help
------------

If you have any problems, questions, feature requests or suggestions, please 
`open a github issue <https://github.com/Pfesi/dran/issues>`_ or `email the author <mailto:pvanzyl@sarao.ac.za>`_.
 

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/interface/cli
   api/interface/gui
   api/interface/web
   tuts/index

   .. tuts/tut_sband
   .. tuts/tut_xband
   .. api/calibration/baseline
   .. api/calibration/rfi
   .. api/fitting/peak
   .. api/fitting/model_and_fit
   .. api/reduction/data_extraction_and_prep
   .. api/vis/stat_anal_and_vis

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Resources:

   api/resources/hart26m
..    api/interface/web
..    api/resources/basics


.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Guidelines:

   caveats

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Changelog:

   extras/CHANGELOG



API Reference
-------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
