# ui/battlemap/tools.py
# Copyright (C) 2018 Alex Mair. All rights reserved.
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

import re
from enum import Enum

from ui.actions import ActionManager, InvalidToolError, ToolBase, tool


class InvalidContractEventError(Exception):
    """

    .. todo::
        Better name.
    """


class FailureMode(Enum):
    """This enum denotes how tools fail when their argument contract is
    violated.
    """

    """Upon failure, the tool cancels itself."""
    cancel = 0

    """Upon failure, the tool does nothing."""
    noop = 1



def maptool(*tool_args, **tool_kwargs):
    return tool(*tool_args, toolcls=MapTool, **tool_kwargs)


class MapTool(ToolBase):
    """

    .. todo::
        Define and document the language surrounding the action method
        parameter names. ``entity\d\?``, ``point_or_entity``, etc.

    """

    param_regexp = re.compile("([A-Za-z]+)[0-9]*")

    def __init__(self, method, *args, view_modes=(),
                 failure_mode=FailureMode.noop, **kwargs):
        super().__init__(method, *args, **kwargs)
        self.contract = MapTool._parse_contract(method)
        self.view_modes = view_modes
        self.failure_mode = failure_mode

    @staticmethod
    def _argmatch(arg):
        match = MapTool.param_regexp.match(arg)
        if not match:
            raise ValueError("improperly formatted identifier `{}'".format(arg))
        return match.group(0)

    @staticmethod
    def _parse_contract(method):
        """Obtain the contract for a given ``method``.

        :param method: The method (annotated using ``@maptool``) that is to have
                       its argument list analysed for a contract.
        :return: A list of strings corresponding to each argument match.
        """
        co = method.__code__
        return [MapTool._argmatch(arg) for arg in
                co.co_varnames[1:co.co_argcount]]


class MapActionManager(ActionManager):
    """The ``MapActionManager`` class offers an convenience for map tools by
    allowing subclasses to implement methods annotated with ``@maptool`` to to
    have their user input requirements automatically determined by the method's
    defining signature.  The list of extracted requirements from a signature is
    called a *contract*, and each requirement in a contract is called a
    *argument match*.

    An argument match is formed by examining the identifier used for the
    parameter. A parameter must consist of a sequence of alphabetic characters
    followed by a series of numbers. The numbers are ignored, and serve only to
    satisfy Python's requirements that parameter names must be unique. The
    sequence of alphabetic characters forms the argument match.

    When a tool is activated, a ``MapActionManager`` instance attempts to
    perform simple lookups on its *delegate*. For each argument match ``X`` in
    the contract, a lookup of ``get_X()`` is performed on the delegate.

    For example, a method that is defined like so::

        @maptool
        def some_tool(point1, point2):
            print(point1 + point2)

    would result in, when the tool is activated, two calls to the delegate's
    ``get_point()``.

    .. todo::
        A contract is basically a tool's state machine. Is it more than linear?

    """

    def __init__(self, battlemap, delegate):
        super().__init__(delegate)
        self.map = battlemap

    def _create_tool(self, toolattr):
        for requirement in toolattr.contract:
            if not hasattr(self.delegate, "get_{}".format(requirement)):
                raise InvalidToolError("requirement `{}' cannot be fulfilled "
                                       "by the delegate".format(requirement))
        return super()._create_tool(toolattr)


class RoadActionManager(MapActionManager):
    @maptool(name="Show nearest entity paths", icon="network")
    def delaunay_single(self, entity):
        """Compute the Delaunay Triangulation for a given Entity."""
        pass

    @maptool(name="Create new road link")
    def new_road(self, entity1, entity2):
        pass


class GeographicActionManager(MapActionManager):
    @maptool
    def select_biome(self, biome):
        pass

    @maptool(icon="brush")
    def paint_biome(self, point):
        pass

    @maptool(name="Pick biome from map", icon="dropper")
    def palette_biome_select(self, point):
        pass
