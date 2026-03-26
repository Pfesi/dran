.. Tutorials for the DRAN program.

Tutorials
=========

The following tutorial will show you how to run a basic data 
reduction for a Hydra A 13 cm or 2 GHz observation. 


Data reduction of 2 GHz data. 
------------------------------

First we need to read in data from the file we want to process 


.. code-block:: bash

  $ dran -path test_data/HydraA_13NB/2011d285_04h55m29s_Cont_mike_HYDRA_A.fits

This will produce the following output 


.. code-block:: bash
    :linenos:

    ************************************************************
    # PROCESSING SOURCE: 
    ************************************************************
    # File name:  2011d285_04h55m29s_Cont_mike_HYDRA_A.fits
    # Object:  HYDRA A
    # Object type:  CAL
    # Central Freq:  2280.0
    # Observed :  2011-10-12
    ************************************************************

    - Processing: ON_LCP


    # No sidelobes detected


    * Center of baseline blocks on left and right of peak: 
    min pos left: [-0.4041615] @ loc/s [160]
    min pos right: [0.391495] @ loc/s [2497]
    scan len: 2699

    # Fit the baseline
    ************************************************************

    # Fit = 0.073x + (-0.034), rms error = 0.0292

    # Fit the peak
    ************************************************************

    # Peak = 2.464 +- 0.030 [K]

    # S/N: 86.77

    - Processing: ON_RCP


    # No sidelobes detected


    * Center of baseline blocks on left and right of peak: 
    min pos left: [-0.40816145] @ loc/s [153]
    min pos right: [0.39016168] @ loc/s [2525]
    scan len: 2731

    # Fit the baseline
    ************************************************************

    # Fit = -0.000632x + (-0.0406), rms error = 0.0254

    # Fit the peak
    ************************************************************

    # Peak = 2.493 +- 0.025 [K]

    # S/N: 100.69

We are now going to breakdown the results returned

Lines 1 - 9 give us basic details on the source under observation.
This includes the name of the file being processed, the object 
being observed, the type of object it is (CAL = Calibrator or 
TAR = Target), the observing frequency, as well as the date the 
source was observed.

Line 11 tells you the drift scan currently being processed, in this 
case its the LCP On scan drift scan.

Line 14 is a debugging output that lets you know if any large sidelobes
were detected, these are sidelobes which are larger than half the peak 
maximum.

Once the data is loaded and prepped, the program begins processing 
the data. First it tries to correct or remove any drift in the data 
that may exists. Using a gradient descent type algorithm, the program 
fits a spline through the data and detects the location of the lowest
minimum locations on either sides of the center of the drift scan.

Line 17 - 20 give us information on the positions selected as the 
local minimum points. An also gives the length of the scan.

4% of the scan length is then used as the number of points required to 
get enough data around the local minimum points in order to fit a 
polynomila therough the data. 

The equation of the line that is used to correct the drift in the data 
is then displayed in line 25.
