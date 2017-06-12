Build prerequisites
===================

.. note::
    This page is out of date. It is kept around because it will be useful
    in the future, but isn't right now.

To build from source, you will need the following libraries and packages
available (verion numbers are minimal requirements):

Python 3.4
pygraph
Python Image Library (PIL)
PyQt5
marshmallow
dateutil

Note that the version numbers below are the minimum I have attempted to run
dmclient with; you are welcome to use older versions but beware
incompatibilities/bugs.


1. Download install Python
2. Download and install sip
   Remember to use: python3 configure.py
3. Download and install Qt5
4. Download and install PyQt5
   Remember to use:
   python3 configure.py --disable=QtPrintSupport \
   --disable=QtDBus --disable=QtSensors --disable=QtSerialPort \
   --disable=QtBluetooth --disable=Enginio --disable=QtWebChannel \
   --disable=QtWebEngineWidgets --disable=QtWebKit --disable=QtWebKitWidgets \
   --disable=QtPositioning --disable=QtXml --disable=QtXmlPatterns \
   --disable=QAxContainer --disable=QtNetwork --disable=QtWebSockets \
   --disable=QtMultimedia --disable=QtMultimediaWidgets
5. Download and install remaining packages from the list above.

TODO
----

Document production builds, as PyQt seems to be built with -g.
