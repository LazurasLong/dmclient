Coding Style
============

Still shaping up, but basically just PEP8.

The following exceptions to PEP8 apply:

* Line length is 80 characters, not 79.
* Docstring length is 80 characters, not 72.

Due to usage of Qt and duck-typing, there are a few additional (and peculiar)
exceptions:

* Signals are always named in ``camelCase``.
* Slot functions are always named ``on_signal_name`` -- i.e., matching the name
  of the signal they are supposed to be connected to, but also in
  ``unix_format``. The exception of course is when the slots are intended to be
  used with ``QMetaObject::connectSlotsByName()``.

As always and/or when in doubt, consistency is key. Match what the existing code
does, even if it is stylistically invalid. It can always be refactored en-masse
later on.

Code Comments
=============

In general, docstrings explain *what* the code does and documents any
assumptions outside of the implementation. Comments explain *why* the
code is written the way it is, and any assumptions that a particular detail
makes.

Avoid redundant docstrings. For example, this is a terrible docstring::

    def build_results_model(self, results):
        """Builds a result model.

        :param results: The results to build the model from.
        :return: A results model.

It is better to omit stupidity like the above rather than include it for
completion purposes.

A slightly better docstring (if indicating the code needs work)::

    def build_results_model(self, results):
        """Constructs a Qt-based model based on ``results``.

        :param results: A dict of category name to lists of ``SearchResult``
                        instances. If the dict is empty, then this method
                        raises ``ValueError``.
        :return: A ``QStandardItemModel`` suitable for tree-views

Notice in this contrived example there are a few pieces of information this
(public-facing) docstring now reveals:

1. The method has an explicit dependency on Qt.
2. The method may throw ``ValueError`` on invalid input.
3. The method returns an instance of ``QStandardItemModel``.
