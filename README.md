# memres_qgisserver
Memory resident QGIS WMS server in python

The factory QGIS server runs as a CGI. This is not suitable for larger projects (many layers, lots of data) due to the slowness of project scanning.
MEMRES is a solution based on a python socketserver that opens a QGIS project file (QGZ) and renders and returns the map in response to WMS calls.

The server must be run from within the QGIS python environment (under windows after osgeo4w.bat)
Usage:
python qgis_memory_wms [qgznev , default: osgeo.qgz] [--savesymb - this option saves the symbols to an images directory)
The server running on port 5000 ( you can change this in the code).


