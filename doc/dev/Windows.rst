Development instructions for Windows
====================================

Currently these are the steps to get going on Windows:

1. Install Python 3.6 and a virtual environment.
2. Install xapian separately.
3. Install MinGW and add `C:\MinGW\bin` to your PATH
4. Launch `cmd.exe` (or Git Bash or whichever) and run `mingw32-make`

.. note::
	This setup is likely to change, nothing is set in stone. It would be nice
	to avoid a dependency on MinGW.
