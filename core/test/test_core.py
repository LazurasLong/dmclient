# core/test/test_core.py
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

import pytest

from core import *


@pytest.mark.parametrize('uuid', [generate_uuid(),
                                  UUID('16fd78c6-827d-4aa0-aaeb-05f25118455c'),
                                  '4a15c11c-4799-4bf7-9fa4-ac0835d3518e'])
def test_isuuid_valid(uuid):
    assert isuuid(uuid)


@pytest.mark.parametrize('uuid', [None, '', 'foobar', [], {}])
def test_isuuid_invalid(uuid):
    assert not isuuid(uuid)


@pytest.mark.parametrize('url,expected',
                         [("file:///", "/"), ("file:///foobar", "/foobar"),
                          ("file:///foobar/baz/bar", "/foobar/baz/bar")])
def test_deurlify_valid(url, expected):
    assert deurlify(url) == expected


@pytest.mark.parametrize('url',
                         ["file://", "foobar", "file:/foobar", "file/foobar"])
def test_deurlify_invalid(url):
    with pytest.raises(ValueError):
        deurlify(url)


def test_hrname_basic():
    assert hrname("test") == "Test"


@pytest.mark.parametrize('attr_name',
                         ["TEST_ATTR", "test_attr", "test attr", "TeSt__ATTR"])
def test_hrname(attr_name):
    assert hrname(attr_name) == "Test Attr"
