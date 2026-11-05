"""Plain HTML building blocks.

NiceGUI's ``ui.row`` and ``ui.column`` carry their own gap and padding, which override Tailwind
utilities. These helpers produce bare tags so layout comes from Tailwind classes alone.
"""

from nicegui import ui
from nicegui.elements.mixins.text_element import TextElement


def box(classes: str = "", tag: str = "div") -> ui.element:
    return ui.element(tag).classes(classes)


def text(value: str, classes: str = "", tag: str = "div") -> TextElement:
    return TextElement(tag=tag, text=value).classes(classes)
