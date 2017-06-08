#!/bin/bash

# TODO: download

cd xapian-core-1.4.4/
./configure
make -j && make install

cd ../xapian-bindings-1.4.4/
./configure --with-python3 --without-python --without-php --without-ruby --without-tcl --without-csharp --without-java --without-perl --without-lua
make -j && make install
