Command-line options
====================

dmclient supports a few command-line switches available on all supported
platforms.

As dmclient is a Qt-based application, it supports all command-line options
listed `here <http://pyqt.sourceforge.net/Docs/PyQt4/qapplication.html#QApplication>`_

.. todo::
        This is not yet implemented and soon should be!

.. cmdoption:: -f <campaign>
        Opens ``<campaign>`` when dmclient has finished loading. This is purely
        for convenience; it does not convey any performance benefit or the like.

.. cmdoption:: --log <level>
        Indicates the verbosity of dmclient's logging. ``<level>`` is one of the
        :ref:`levels supplied in the Python standard library <python:_levels>`

.. cmdoption:: --max-frames FRAMES
        Cap the number of frames the VBM runs at. ``1 <= FRAMES <= 60``

.. Not yet:
        .. cmdoption:: -cb TYPE
                  Enable colour blind support. FIXME - what types?
