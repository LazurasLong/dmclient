Building and running dmclient
=============================

1. :doc:`Install a virtual environment </dev/VirtualEnvironment.rst`.
2. Activate it.
3. Run ``make``. It should do everything for you.
4. Set ``PYTHONPATH`` to the source checkout.
5. ``python3 dmclient.py`` (or just ``./dmclient.py``).

By default, many of the loggers are noisy. Also, unless I am working on the
oracle I don't really need it running. As a result, I tend to use this
invocation, specifically placed within a PyCharm Run Configuration::

   dmclient.py -c resources/test/protege/testcampaign.dmc --log model.qt=warn ui.schemamap=warn --disable-oracle

Due to the virtual environment and the ``PYTHONPATH`` hackery, I have a bash
alias setup::

   alias dmc='cd ~/txt/hacking/dmclient ; echo $PATH | grep -q dmclient-venv || { export PYTHONPATH=$PWD ; source ../dmclient-venv3.6/bin/activate ; }'
