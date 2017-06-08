dmclient's Virtual environment
==============================

Using a Python virtual environment is the easiest way to start hacking on dmclient.

To create a new virtual environment, run the following bash script from within a dmclient checkout::

    #!/bin/bash
    [ ! -e "dmclient.py" ] && {
        echo error: please invoke me from a dmclient checkout. >&2
        exit 1
    }

    DMC_VENV_DIR="${DMC_VENV_DIR:=../dmclient-venv}"

    virtualenv -p python3.6 --prompt='(dmc)' "${DMC_VENV_DIR}"
    source "${DMC_VENV_DIR}/bin/activate"
    pip3.6 install -r requirements.txt

**Please note** that not all of dmclient's requirements may be satisfied via ``pip``. In particular, Xapian is not fulfilled; either install Xapian manually or pass ``--disable-oracle`` when invoking dmclient.
