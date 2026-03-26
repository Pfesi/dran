Quickstart Guide
=================

After the successful `installation <installation.rst>`_ of the 
package libraries you can now start reducing the data. DRAN provides 
you with a variety of options to process drift scan data which are
discussed below.

Getting help
------------

As a beginner, it is advised to start running your analysis by 
basically just loading the program helper. This is useful as it 
starts the program and shows you the commands available to you. 

To start the program type 

.. code:: python

   dran -h 

This command starts the program and displays a set of options a user 
can select to begin processing drift scan data. :: 


   usage: DRAN [-h] [-path PATH] [--debug] [--saveplotstodb] 
               [-mode {auto,gui,web,anal,docs,serve}] [-threads THREADS] 
               [-port PORT] [-workdir WORKDIR] [-v]

   Begin processing HartRAO drift-scan data from the Hart 26m telescope.


   options:
   -h, --help            show this help message and exit
   -path PATH, --path PATH
                           Path to a FITS file or directory containing FITS
                           files. (default: None)
   --debug               Enable debug logging. (default: False)
   --saveplotstodb       Save plot data / lightcurves in the database. Bloats the
                           database. (default: False)
   -mode {auto,gui,web,anal,docs,serve}, --mode {auto,gui,web,anal,docs,serve}
                           Operating mode. (default: auto)
   -threads THREADS, --threads THREADS
                           Number of worker threads. (default: None)
   -port PORT, --port PORT
                           Port number for web interface. (default: 4000)
   -workdir WORKDIR, --workdir WORKDIR
                           Working/results directory. (default: DRAN_RESULTS)
   -v                    show program's version number and exit
   --remote-paths REMOTE_PATHS
                           Remote path to process. Repeat for multiple paths.
                           Examples: --remote-paths Continuum --remote-paths
                           data/Calibrators --remote-paths /data/pks0454-234
                           (default: [])


.. warning::
   -threads is not implemeneted yet, and --remote-paths is not implemented in the 
   public version of dran.


Running the program
-------------------


Processing a single file  or directory ::
************************

   dran --path data/HydraA_13NB/2014d047_20h30m12s_Cont_mike_HYDRA_A.fits

   or

   dran --path data/HydraA_13NB/

Adding debugging to a file or directory ::
***************************************

   dran --path data/HydraA_13NB/ --debug

Saving processed plots to the database ::
**********************************

   dran --path data/HydraA_13NB/ --saveplotstodb

Saving to a specific directory::
***********************

   dran --path data/HydraA_13NB/ -workdir my_special_dir

Viewing the docs ::
****************

   dran --mode docs

Showing program version ::
***********************

   dran -v
