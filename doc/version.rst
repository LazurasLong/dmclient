**********************
Versioning in dmclient
**********************

dmclient obeys the following rules when it comes to identifying individual
releases by their *version*. dmclient versions take the form ``X.Y.Z``, where
``X`` is the major integer, ``Y`` the minor integer, and ``Z`` the release
integer.

.. note::
    In this document, "user data" refers to both game system and campaign
    data.

As hinted in the following sections, the version is largely driven by two
factors: compatibility with permanent user data and the user interface.

Major releases
==============

Major releases in dmclient correspond to *incompatible* releases with respect
to storing and saving user data. dmclient is not expected to remain compatible
with data from differing major revisions. There may exist a mapping of data
from major versions of dmclient and even a realised implementation of this
mapping, but dmclient is not expected to support this internally. Indeed, the
characteristic of this mapping is that it is partial, so dmclient *cannot*
support it internally (i.e., dmstudio is required), or unstable, so dmclient
*shouldn't* support it.

Major releases should be reserved for large changes to the user interface.

Minor releases
==============

Minor releases indicate a *stable*, *non-destructive* mapping between user data
formats. dmclient is to automatically convert the user's data upon loading an
archive, but **not** to overwrite the information on permanent storage without
the user's permission.

Minor releases should not see large changes to the user interface; a user
should not be expected to re-learn how to use dmclient upon a minor release. It
is acceptable if a user has to re-learn some small component of dmclient, such
as using a particular graphical window for a feature.

Minor releases may include any number of features of varying size provided that
they do not result in many changes to the user interface. Since dmclient is a
graphical program this will rarely be the case, but it is worth making
explicit. For example, suppose some large component of dmclient is rewritten
(possibly in another programming language!), thus instigating large-scale
changes to the codebase. If the user interface does not need to be changed to
reflect the new component, then it may still be included in a minor release of
dmclient.

Release number
==============

Release numbers correspond to smaller feature tweaks and bug fixes. Conversions
between user data formats is forbidden. User interface changes should be
polish-only; no functionality should be removed or added upon a release.
