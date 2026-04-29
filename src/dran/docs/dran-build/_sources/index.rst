DRAN documentation
================================

Introduction
------------

``DRAN`` is a data reduction and 
analysis python software package developed for the systematic processing of 
single-dish drift scan data from `HartRAO's 26m telescope <http://www.hartrao.ac.za/hh26m_factsfile.html>`_. 
It was developed to replace the legacy ``LINES`` software previously 
used at the `Hartebeesthoek Radio Astronomy Observatory <http://www.hartrao.ac.za/>`_. 

The package is implemented in `Python 3.11 <https://www.python.org/downloads/>`_ and provides 
tools for simple data processing, including:

- :doc:`api/reduction/data_extraction_and_prep`
- :doc:`api/fitting/model_and_fit`
- :doc:`api/vis/stat_anal_and_vis`

``DRAN`` is intended for both calibrator and target source analysis, with an emphasis 
on reproducibility, automation, and traceability of results. 


.. Final fit parameters, diagnostics, and derived statistics are written to an 
.. `SQLITE <https://sqlite.org>`_ database for later analysis. All plots generated 
.. during processing are saved to the ``PLOTS`` directory created in the ``current 
.. working directory``.



Interfaces
----------

DRAN supports 4 primary interfaces:

- :doc:`api/interface/cli`, intended for automated and batch processing.
- :doc:`api/interface/gui`, intended for interactive inspection, fitting, 
  and time-series analysis of individual observations.
- :doc:`api/interface/web`, currently in development.
- ``docs``, this documentation.


.. Ports
.. -----

.. To run this documentation interface, the port defaults to port 4000. This can be 
.. changed using 

.. .. info:: bash
..    dran --mode docs --port new_port_number


.. .. warning::
..    The new_port_number should be an integer.


What's next ?
-------------

.. - For a basic understanding of the radio astronomy backgound for these observations, 
.. see :doc:`extras/notes/radio_astro`.

- To understand the workflow in practice, start with the tutorials in :doc:`tuts/index`.

- Installation instructions are provided in :doc:`installation`.

- Before performing scientific analysis, users are strongly encouraged to review :doc:`caveats`, which outlines assumptions, limitations, and known constraints.



Acknowledging DRAN
-------------------

If you use DRAN in a publication, please cite `van Zyl P. 2023 <https://ui.adsabs.harvard.edu/abs/2023arXiv230600764V/abstract>`_.


Getting help
------------

If you have any problems, questions, feature requests or suggestions, please 
`OPEN AN ISSUE <https://github.com/Pfesi/dran/issues>`_.
 

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   tuts/index
   tuts/tut_sband
   tuts/tut_xband
   api/calibration/baseline
   api/calibration/rfi
   api/fitting/peak
   api/fitting/model_and_fit
   api/reduction/data_extraction_and_prep
   api/vis/stat_anal_and_vis

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Resources:

   api/interface/cli
   api/interface/gui
   api/interface/web
   api/resources/basics


.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Guidelines:

   caveats
   extras/CHANGELOG



API Reference
-------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
