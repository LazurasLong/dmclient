# ui/schemamap.py
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

from logging import getLogger

from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtWidgets import QDataWidgetMapper, QLineEdit, QCheckBox, QSpinBox, \
    QLabel, QPlainTextEdit
from marshmallow import fields

log = getLogger(__name__)


marshmallow2qwidget = {
    fields.String:          (QLineEdit, QPlainTextEdit, QLabel),
    fields.FormattedString: QLineEdit,
    fields.Boolean:         QCheckBox,
    fields.Integer:         QSpinBox,
    fields.Float:           QSpinBox,
    fields.DateTime:        QLabel,
}


def schema_ui_map(schema, model, form):
    """Construct a QDataWidgetMapper from the given ``schema`` class.

    :param schema: The schema to create field-to-widget mappings from.
    :param model: The model that the QDataWidgetMapper observes.
    :param form: The UI widget containing stuff to bind to. It is also set as
                 the parent for the widget mapper.
    """
    assert isinstance(model, QAbstractItemModel)
    mapper = QDataWidgetMapper(form)
    mapper.setModel(model)

    s = schema()

    for i, (name, field) in enumerate(s.fields.items()):
        try:
            widget_classes = _widget_type(type(field))
            widget = form.findChild(widget_classes, name)
            if not widget:
                raise ValueError
            prop = _widget_property(type(widget))
            log.debug("adding map from (`%s', col = %d) to %s (prop = `%s')",
                      name, i, widget, prop)
            mapper.addMapping(widget, i, bytes(prop, encoding='utf8'))
            assert mapper.mappedWidgetAt(i) == widget
        except KeyError:
            log.error("unknown field type %s", type(field))
        except ValueError:  # FIXME: is this the correct exception type?
            log.error("failed to find widget for field `%s'", name)

    mapper.toFirst()
    return mapper


def _widget_type(fieldtype):
    # TODO: readonly -> qlabel?
    if fieldtype == fields.Nested:
        raise ValueError("I don't know what to do!")
    return marshmallow2qwidget[fieldtype]


def _widget_property(widget_type):
    # TODO: Why aren't we just using the USER property?!
    return {QPlainTextEdit: "plainText",
            QLabel:         "text",
            QLineEdit:      "text",
            QCheckBox:      "checked",
            QSpinBox:       "value"}[widget_type]
