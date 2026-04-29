.. The caveats page

Caveats
========

It is highly recommended that you familiarize yourself with 
this page before starting any data reduction or analysis. This list here 
is not an exhaustive list and will be updated on a case by case basis.

**Operating systems**

This code has only been tested on MacOS and Linux systems. There is no provision 
at the moment for Windows systems.

**Help options**

Although there are multiple options you can select to run your data processing, 
they can not all be run simultaneously. For detailed information on how to 
use the options please refer to the `Tutorials <tuts/tutorials.rst>`_ .


**Documentation**

The docs are hard-wired to operate on port 4000. If another process is running on 
the same port, that process is immediately killed to make space for the docs.

This process however doesn't always work, I discovered a bug that may fail to load 
the docs, if you encounter an error message to this effect, just re-run the command.

.. **Order of commands when running the program** 

.. .. warning::
..     COMPLETE THIS!

.. The program may fail or refuse to process the data if the order of the commands
.. is not placed appropriately. For example, this will run

.. but this 

.. will produce the following error.

.. The above error showing up does not mean the program doesn't work. Its basically a warning
.. telling you you need to rearrange the way you wrote your commands. What seems to work best is 
.. writing the command for reading in the file first then all the other extra commands after that.
.. Not sure why this bug exists as yet.

.. **Processing data from tiered directory**

.. .. warning::
..     TRYING TO FIX THIS! as soon as possible
    
.. If for instance you have file located in data/files/more_files/file.fits . And there are 
.. also some other fits files in data/files/ . The program will try to process all the files
.. in data/files/ that are .fits files first, then try to process your file in data/files/more_files/ .
.. This tiered nature causes issues where the program fails to detect whether if has processed files
.. in data/files/more_files/ or data/files/ leading to the program repeat fitting files that have 
.. already been processed and completely skipping others that have not been processed at all.
.. This is a bug I am aware of but have not begun fixing yet. For best results make sure the file 
.. or files you are trying to process follow the folder/*.fits file path format or just get the direct path 
.. to the specific file you want.
 
.. **The dashboard**

.. When opening the dashboard, if the dashboard doesn't open immediately
.. or you get a server not found error you may need to refresh the page
.. so that the dashboard can show up on your screen.


.. **Processed data storage**

.. Currently the program only stores processed data in an `SQLite <https://www.sqlite.org/index.html>`_ database. 
.. The CALDB database stores calibrated data, this is all data from HartRAO monitored calibrators. Contact the author 
.. to get a list of these calibrators if you are unsure. The TARDB database stores all the processed target source 
.. information. These are sources that do not fall into the known calibrator list. If you process a source that is 
.. not in the HartRAO list of calibrators, this source will be treated as a target source and all the processed 
.. information will be stored in the TARDB database. Support for MySQL has not been implemented yet but will be 
.. in a future release.


.. **Database error on initial run**

.. When you run the code for the first time, because there will be no 
.. database created and the following warning will pop up

.. .. warning::

..     Failed to read FILENAME column from table 'TABLENAME', the table either doesn't exists or is corrupted.

.. This warning will not stop the processing of data and the code will continue to run as per normal. In consequent runs this warning will no longer appear.

.. **Database analysis**

.. Analysis on sources default to Hydra A as the main calibration source. To 
.. select own calibrator it s advised to use the gui timeseries editor.

.. .. note::

..     Special cases with regards to observations exists. These cases are mainly concerned 
..     with different projects that are done to test certain properties of the telescope. 
..     The analyses of any calibrator contains only that data considered to be normal data. Instances 
..     where certain things are beign tested, e.g. gain curve calibration, and these data are recorded 
..     in the database, then these are ignored. 

.. **Memory allocation**

.. The program focus at the moment is to ensure the correct output is delivered to the user. This 
.. causes problems with memory allocation when running large batch analysis processes. For MacOS 
.. users you may get a "Your system has run out of application memory error" during processing. To 
.. solve this problem, clear the python application and restart the analysis. Unfortunately this 
.. problem can only be addressed in future releases.