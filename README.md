# IMRT-QA-Data-Miner
Scans a directory for IMRT QA results.

### Install
~~~~
$ pip install IQDM
~~~~

### How to run
~~~~
$ IQDM <initial-scan-dir>
~~~~

### Notes
This script was written specifically for SNC Patient and Delta4, but I'd be happy to include support for other vendors 
if someone could provide some anonymized example reports.

### Contributing
If you'd like to contribute code to support a new vendor, please create a new python file in the parsers directory 
containing a new class. This class should include the following to be compatible:

* **PROPERTIES**
    * **identifiers**  
    this is a list of strings that collectively and uniquely are found in a report type
    * **columns**  
    a list of strings indicating the columns of the csv to be output
    * **csv**  
    a string of values for each column, delimited with DELIMITER in utilities.py
    * **report_type**  
    a string succinctly describing the report, this will be used in the results filename created in main.py

* **METHODS**
    * **process_data(text_data)**  
    processing the data does not occur until this is called
