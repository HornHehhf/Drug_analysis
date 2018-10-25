1. Install Python language on computer.
==================================================

1.1 Download Miniconda python 2.7 32bit on following link to install Python.

https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86.exe

This is for Windows, other versions please refer to http://conda.pydata.org/miniconda.html

1.2 Install modules:

Running following in an command line window.
(Double click file command.bat in project folder to do quickly, or any ways whatever you like.)
(Must have Miniconda installed.)

conda install lxml
------------------

2. Running process
==================================================
Running as:

python scrape_url.py "url_of_search"
------------------------------------

or specify time span:
python scrape_url.py "url_of_search" 2013-01-01,2013-12-31 
----------------------------------------------------------

2.1 Proxy
Set up proxy server at lines 29-30 in file scrape_url.py
Insert "#" ahead the line 32 to enable proxy.

3. Files Description
==================================================

scrape_url.py ==> scraping routine.

command.bat ==> double click to open a command line window quickly.

logging.txt ==> running info.

html ==> folder to save documents with HTML format.
text ==> folder to save documents with TEXT format.
doc ==> folder for readme.


