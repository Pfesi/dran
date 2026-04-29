DRAN README
===========

**DRAN** (**D**ata **R**eduction and **AN**alysis) is the 
software pipeline  developed to streamline the reduction and 
analysis of drift scan data acquired 
with [HartRAO's ](http://www.hartrao.ac.za) [26m telescope](http://www.hartrao.ac.za/hh26m_factsfile.html). DRAN supersedes the older **LINES** continuum data reduction and analysis program previously employed at HartRAO.

To get started with DRAN and read more on the full documentations of the 
program you can go to the 
DRAN [READ THE DOCS](https://dran.readthedocs.io/en/latest/) page.

Acknowledging DRAN
-------------------
To acknowledge the **DRAN** software pipeline, please 
cite [van Zyl P. 2023](https://ui.adsabs.harvard.edu/abs/2023arXiv230600764V/abstract).  For a full citation, you can reference the following publication: arXiv:2306.00764 [[astro-ph.IM]](https://arxiv.org/abs/2306.00764).

Program structure 
------------------

**DRAN** offers two user interfaces:

* **Command-Line Interface (CLI)**: Designed for automated and semi-automated processing of drift scan data. The CLI streamlines the reduction and analysis of large batches of drift scan files.

* **Graphical User Interface (GUI)**: Provides a user-friendly environment ideal for interactive exploration and analysis of individual files. The GUI allows for data inspection, fitting, and basic analysis of time series data produced by the CLI.



Requirements
-------------

The list of required Python packages can be found in 
the included requirements.txt file.


Installation 
-------------

DRAN is conveniently available for installation through 
the [PYPI package manager](https://pypi.org/project/dran/) using 
the following command:

``` 
  $ pip install dran
```

Data files
----------

### Input Data Format

DRAN requires data to be provided in the Flexible Image Transport 
System [FITS](https://fits.gsfc.nasa.gov/fits_documentation.html) format, 
a common standard for scientific data.



### File Reading Methods:
DRAN offers two ways to specify input data:

1. Explicit File Path: Users can provide the complete path to a single FITS file or a directory containing FITS files for batch processing.

```
Example: 
$ dran -path /path/to/single_file.fits
```
```
Example (batch processing): 
$ dran -path /path/to/data_directory/
```

2. Interactive Selection (GUI only):  The graphical user interface (GUI) allows users to interactively browse and select individual FITS files for processing.

### Output Data Format

DRAN stores the processed data in a SQLite database file. This file is automatically saved in the user's current working directory upon completion.


Getting Started with DRAN
----------
Once you've installed DRAN, you can start processing your data. Here's a quick guide to get you started:

1. Explore available options:

Run the following command to see a list of available options and what they do:

```
$ dran -h or --help
```

2. Process your data:

Use the -path option followed by the path to your data to process a single file or an entire directory:

* To process a single file:
```
$ dran -path /path/to/your/file.fits
```

* To process all FITS files in a directory (batch processing):

```
$ dran -path /path/to/your/data/directory/
```

* To run the GUI
```
$ dran-gui 
```


1. Additional options:

For more advanced users, the -debug, -saveplotstodb, -port, and -mode options provide additional functionalities. Refer to the full help menu (dran -h) for detailed explanations.

> `note:` If you have suggestions for new features, feel free to contact the author (details provided below).

Important Considerations:
-------

While DRAN strives to provide good quality fits to your data, it's important to be aware of the following:

* Automatic Fitting: DRAN performs automated fitting routines. However, it's crucial for users to visually inspect the results to ensure a satisfactory fit.

* Data Quality: DRAN attempts to fit all data points, including potentially problematic ones. Users should be mindful of potential outliers or noise in their data that might affect the final fit.

Recommendation:
-------
To ensure accurate analysis, we recommend that users review the generated plots located in the "plots" folder. These plots visually represent the fit and can help identify any potential issues with the data or the fitting process.


Get Help and Contribute
---------------

Having trouble with DRAN? Have questions about the software or features? We encourage you to:

* Report Issues: Encounter any bugs or unexpected behavior? Please [OPEN AN ISSUE](https://github.com/Pfesi/dran/issues) on the GitHub repository.
* Share your thoughts: We value your feedback! Feel free to use the GitHub issue tracker to suggest improvements or request new features.

