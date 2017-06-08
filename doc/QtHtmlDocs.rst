Do this on Linux Mint distributions to make the html docs suck less:

$ sudo mv /usr/share/doc/qt5-doc-html{,~}
$ sudo ln -s /usr/share/qt5/doc /usr/share/doc/qt5-doc-html

