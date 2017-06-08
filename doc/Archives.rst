dmclient Archives
=================

Archives are the core of dmclient's persisted storage. Each archive is
identified by a UUID. See `Archive Metadata <Metadata.rst`_ for more information
on the metadata associated with each archive.

Rules archives
==============

Currently, dmclient only has two types of rules archives.

Game libraries
--------------

A game library is the smallest unit of rules and assets that a game requires to
function at a realistic level. Most systems have a "core rulebook", some,
notably D&D, have their rules spread across multiple books. A game library is
intended to represent a watered-down version of this rulebook (mostly for legal
reasons). In the case of systems that have their core rules spread across
multiple books, a game library is intended to represent an amalgamation of these
books.

Note that a game libraries potentially have a many-to-one mapping to a game
system, but only one game library may be used by session in dmclient at any
point in time.

Game expansions
---------------

This is any set of rules and assets that are not required for base play.
Typically these correspond to extra published materials.

Game expansions always build on top of a game library, and thus require one for
play. Expansions may override the rules or assets present in a library or even
other expansions. However, dmclient forbids cycles in dependencies or
overridding assets.

User archives
=============

Currently dmclient only knows about one type of user-supplied archive.

Campaign archives
-----------------

These archives capture the essence of session-to-session interaction of
dmclient. More to follow.
