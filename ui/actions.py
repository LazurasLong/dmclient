# ui/actions.py
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

"""This module provides... something. Some kind of ``QAction`` and ``QToolBar``
thing, currently.

"""

import inspect
from logging import getLogger

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction, QActionGroup

from core import attrs, hrname

__all__ = ["ActionManager",
           "ToolBase",
           "tool",
           ]

dummy_icon = None
log = getLogger(__name__)


class InvalidToolError(Exception):
    pass


class AbortedAction(Exception):  # TODO: better name. Not an exception?!
    pass


def _load_icon(name):  # FIXME
    icon_path = ":/icons/{}.png".format(name)
    log.debug("attempting to load `{}'".format(icon_path))
    pixmap = QPixmap(icon_path)
    if pixmap.width() < 1:
        log.error("no such icon defined, using dummy")
        global dummy_icon
        if not dummy_icon:
            dummy_icon = QIcon(":/icons/dummy.png")
        return dummy_icon
    return QIcon(pixmap)


class ToolBase(QObject):
    def __init__(self, action, name="", icon=None, group="", **kwargs):
        super().__init__()
        self.action = action
        self.group = group
        self.icon_name = icon if icon else action.__name__
        self.manager = None
        self.name = name if name else hrname(action.__name__)

    def __repr__(self):
        group = "<no group>" if not self.group else self.group
        return "<ToolBase({}, {}, {}, {})>".format(self.name, self.icon_name,
                                                   group, self.action)

    def activate(self, *args, **kwargs):
        try:
            self.action(self.manager, *args, **kwargs)
            log.debug("tool `{}' triggered".format(self.name))
        except AbortedAction as e:
            log.error("The action was aborted: %s", e)


def tool(*tool_args, toolcls=ToolBase, **tool_kwargs):
    """The ``@tool`` decorator is for (hopefully) nice magic of stuff.

    It turns the decorated function into a ``ToolWrapper`` (command-pattern)
    which allows for all kinds of fancy things with subclasses and shit.

    """
    # Argument-less decorator
    if len(tool_args) == 1 and inspect.isfunction(tool_args[0]):
        return toolcls(tool_args[0])

    # Otherwise, someone was passed arguments.
    def tool_wrapper(action):
        tool = toolcls(action, *tool_args, **tool_kwargs)
        return tool

    return tool_wrapper


class ActionManager(QObject):
    """This class is an abstract foundation for conveniently managing toolbars,
    through objects derived from ``ToolBase``, herein called "tools".

    Tools may be persistent ("activated") and mutually exclusive, indicated by
    a subclass settings ``exclusive`` to ``True``. The resulting ``QAction`` has
    its ``checkable`` property set.

    Inherits from ``QObject`` so that subclasses may use slots. (um, why?)

    .. todo::
        De-couple this class from Qt. Was thinking of something like
        ``populate_toolbar(toolbar, action_factory)`` instead of
        ``toolbar(parent)``.

    """
    exclusive = False

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.tools = []
        self._action_group = None  # FIXME this is stupid.
        self._build_tools()

    def _methods_annotated_with_tool(self):
        """Factory method pattern for obtaining the list of ``@tool`` annotated
        methods on this ``ActionManager``.

        Subclasses may re-implement this method to control... what, exactly?

        """

        for attr_name, attr in attrs(self.__class__).items():
            if not isinstance(attr, ToolBase):
                continue
            yield attr

    def _build_tools(self):
        for attr in self._methods_annotated_with_tool():
            try:
                tool = self._create_tool(attr)  # FIXME this stuff is weird
                self.tools.append(tool)
            except InvalidToolError as e:
                log.error("invalid tool: %s", e)

    def _create_tool(self, toolattr):
        toolattr.manager = self
        return toolattr

    def action_group(self, parent):
        self._action_group = QActionGroup(parent)
        for tool in self.tools:
            action = self._create_action(tool, self._action_group)
            action.setCheckable(True)
            def f():
                self.delegate.selected_tool = tool
            action.triggered.connect(f)
        return self._action_group

    # noinspection PyMethodMayBeStatic
    def _create_action(self, tool, parent):
        icon = _load_icon(tool.icon_name)
        action = QAction(icon, tool.name, parent)
        return action


class CompositeActionManager(ActionManager):
    """Composite-pattern class to handle interactions between different
    ``ActionManager`` groups.

    .. todo::
        Implement this class and use it to handle a given toolbar's state
        w.r.t. the visual look of the buttons.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.managers = []
