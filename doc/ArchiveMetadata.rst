Archive metadata
================

Archive metadata is information required by dmclient to identify an archive. In
addition to the traditional role of metadata of providing cateloguing
information, it is also used to ensure that only compatible archives are used
together.

For example, one may not combine rules from two different game systems. Metadata
is used to enforce this restriction via the ``Game system`` key.

Metadata is presented in-source as regular Python dictionaries. (They may not
actually be implemented as such, but one can expect them to work as expected.)

The following metadata keys are currently recognised by dmclient:

Name
    A human-friendly name that encapsulates what the archive contains. This is
    used solely for presentation purposes and thus may not be unique (or even
    specified!)

    Typical use is as follows: for libraries and expansions, it corresponds to a
    published book or source. Campaigns typically use the name as whatever the
    owning GM wishes it to be.

Creation date, revision date
    When the archive was created and last modified respectively. Note that
    dmclient does not enforce these values in any way!

License
    This metadata key is only used by rules archives.

Game system
    TODO.
