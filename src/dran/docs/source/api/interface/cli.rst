The command line interface (CLI)
================================

In this mode data can be processed in either automated or manual 
mode. In automated mode, the user has the option to process the data 
using the predefined data reduction method "dran-auto" using the prompt 

.. code:: 

  $ dran-auto path_to_file

  or 

  $ dran-auto path_to_folder

This option automatically selects and locates all the required fitting 
parameters including the positions and locations of the baseline blocks 
and the position of the peak. The default fitting methods for the data 
performs a 1st order fit to the baseline blocks and a 2nd order polynomial 
fit for the peak. This processing method can also be semi-automated allowing for
minor changes which can be found in the help resource which can be accessed using the 
following prompt

.. code-block:: 

  % dran-auto -h          

  usage: DRAN-AUTO [-h] [-db DB] [-f F] [-delete_db DELETE_DB] [-conv CONV]
                  [-quickview QUICKVIEW] [--version]

  Begin processing HartRAO drift scan data

  optional arguments:
    -h, --help              show this help message and exit
    -db DB                  turn debugging on or off. e.g. -db on, by default debug is off
    -f F                    process file or folder at given path e.g. -f
                            data/HydraA_13NB/2019d133_16h12m15s_Cont_mike_HYDRA_A.fits or -f
                            data/HydraA_13NB
    -delete_db DELETE_DB    delete database on program run. e.g. -delete_db all or -delete_db CALDB.db
    -conv CONV              convert database tables to csv. e.g. -conv CALDB
    -quickview QUICKVIEW    get quickview of data e.g. -quickview y
    --version               show program's version number and exit


On the other hand manual mode gives the user total autonomy on the drift scan 
reduction process. However, this implementation has not been activated yet.

The following tutorial will show you how to process data in semi-automation.

automated data reduction
------------------------------

Semi-automated data reduction involves typing in commands to 
run certain types of analysis using the program. This is the 
prefered mode of data reduction as it caters for both single 
and batch mode data analysis.

Before starting any analysis it is recommended that you first 
read the help doc to familiarize yourself with the basic commands  
required to perform data analysis with DRAN. This is done using

.. code-block:: bash 

  $ python dran.py -h


The above line of code outputs the following:


.. code-block:: bash
  :linenos:

  usage: dran.py [-h] [-db DB] [-f F] [-force FORCE] [-c C] [-b B] [-delete_db DELETE_DB] [-mfp MFP]
  [-keep KEEP] [-delete_from DELETE_FROM] [-conv  CONV]

  Begin processing HartRAO drift scan data

  optional arguments:
    -h, --help            show this help message and exit
    -db DB                turn debugging on or off. e.g. -db on, by default
                        debug is off
    -f F                  process file or folder at given path e.g. -f data/Hydr
                        aA_13NB/2019d133_16h12m15s_Cont_mike_HYDRA_A.fits or
                        -f data/HydraA_13NB or -f data/
    -force FORCE          force fit all drift scans y/n e.g. -force y. Default
                        is set to n
    -c C                  initiate the command to run program. e.g. -c gui or -c
                        run_auto_analysis or -c cmdl
    -b B                  initiate browser. e.g. -b docs or -b dash
    -delete_db DELETE_DB  delete database on program run. e.g. -delete_db y
    -mfp MFP              multi-file processing of data between two dates. e.g.
                        -mfp fileList.txt
    -keep KEEP            keep original plots while processing data. e.g. -keep y
    -delete_from DELETE_FROM
                          in coordination eith the filename, use delete_from to delete a row from a database
                          e.g. delete_from CALDB
    -conv  CONV           convert the database tables to csv. e.g. conv y

Depending on the process you want to run, you can select one or 
more of the available options. If there are more options you would 
like implemented please email the author.

To perform an automated data reduction process on a single file

.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits


if you want to set debuggin on

.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -db on


To force a fit on all drift scans, especially those that the 
program would generally categorize as bad scans and not fit them


.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -db on -force y


To delete both the calibration and target databases everytime the 
program starts


.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -delete_db y


To process multiple chunks of data within seperate periods of the 
year you use the following command

.. code-block:: bash 

  $ python dran.py -mfp file_list.txt

.. note::
  
   This assumes that there exists a file called 
   fileList.txt in the current directory that has the full path 
   to the folder containing the source fits files you want to 
   process. This file also has a start and end date in "YYYYdDDD" 
   format stipulating the data range you want to process.  

To process all the data located in your directory, this is the 
directory that contains all the folders containing your fits files

.. code-block:: bash 

  $ python dran.py -f path-to-directory


To run data reduction using the GUI

.. code-block:: bash 

  $ python dran.py -c gui

To run data reduction using the GUI with a pre-selected file

.. code-block:: bash 

  $ python dran.py -c gui -f path-to-file

To initiate the browser to view the analyzed data on a dashboard


.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -b dash


To view the web documentation guide of the software


.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -b docs


To run the semi-automated data reduction process through the 
command line


.. code-block:: bash 

  $ python dran.py 


and follow the prompts. This will bring up the menu shown below 
with options to select how you want to proceeed with your data 
reduction or analysis. 

.. code-block:: html
  :linenos:

  ##################################################################
  # 								                                 #
  # 		 ######  ######  ###### #    #  		                 #
  # 		 #     # #    #  #    # # #  #  		                 #
  # 		 #     # #####   ###### #  # #  		                 #
  # 		 #     # #    #  #    # #   ##  		                 #
  # 		 ######  #    #  #    # #    #  		                 #
  # 								                                 #
  ##################################################################

  #	 PROGRAM STARTED


  ## SELECT OPTION:
  ----------------------------------- 

   1. Data reduction
   2. Open GUI
   3. Run command line analysis
   4. Open documentation
   5. Open dashboard
   6. Exit program

   Please select an option

   Option Selected: 



To process data using the gui

.. code-block:: bash 

  $ python dran.py -f path-to-file/filename.fits -c gui


Manual data reduction
----------------------

This has been implemented but not complete for testing yet. 