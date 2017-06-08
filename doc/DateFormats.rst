Storing dates in dmclient
-------------------------

dmclient generally deals with two types of documents:

1. Human-readable, when space is not a concern.
2. Machine-friendly (likely compressed), when space is a concern.

In either document, date- or time-stamps may be required; in fact it is pretty
much a guarantee in either case. However, handling dates is notoriously prone
to coding errors.

dmclient thus mandates the following:

1. For human-readable documents ISO-8601 is required. See [1]_.
2. Machine-friendly documents can use UNIX timestamps.


.. [1] https://en.wikipedia.org/wiki/ISO_8601
