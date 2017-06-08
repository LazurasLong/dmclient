# core/math.py
# Copyright (C) 2017 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

"""This module provides mathematical functions that operate on integers
and floating point numbers.

"""

import math

__all__ = ["clamp", "next_multiple", "previous_multiple"]


def clamp(x, x_min, x_max):
    """Clamp a value. Equivalent to: ``max(x_min, min(x_max, x))``"""
    return max(x_min, min(x_max, x))


def multiple(f, a, base, k):
    assert 0 < base
    # TODO: This feels dumb, can we have a better algorithm? (logarithms?)
    return int(base * (f(a / base) + k))


def previous_multiple(a, base, k=1):
    """Given ``0 < base``, return the highest integer ``x`` such that ``x <= a``
    and ``base mod x == 0``.

    """
    return multiple(math.floor, a, base, -k+1)


def next_multiple(a, base, k=1):
    """Given ``0 < base``, return the lowest integer ``x`` such that ``a <= x``
    and ``base mod x == 0``.

    """
    return multiple(math.ceil, a, base, k-1)
