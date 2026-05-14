Installation 
============

.. note::
   ``DRAN`` has not been tested on any previous python versions. And 
   there is no support for backwards compatibility.

   `Please report any issues to github <https://github.com/Pfesi/dran/issues>`_

These instructions will install ``DRAN`` as well as its dependencies.

The recommended way to install ``DRAN`` is by using pypi or the `pip <https://pypi.org/project/pip/>`_ 
package manager using the command

.. code-block:: bash

   pip install dran


``DRAN`` can also be installed using the `uv <https://docs.astral.sh/uv/>`_ package 
management system using the command

.. code-block:: bash
   
   uv run dran

Check the installation
-----------------------

After installation, check that the ``DRAN`` command is available:

.. code-block:: bash

   dran -help 