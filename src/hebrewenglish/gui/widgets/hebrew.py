import html

from nicegui import ui

from hebrewenglish.gui.model import ResolvedForm, highlight_segments
from .elements import text

_SEGMENT_CLASSES = {"root": "", "inflection": "morph-inflection", "suffix": "morph-object-suffix"}


def hebrew_text(value: str, classes: str = "", tag: str = "span") -> ui.element:
    """Right-to-left text in the pointed Hebrew font."""
    return text(value, f"hebrew-text {classes}", tag).props("lang=he dir=rtl")


def highlighted_form(resolved: ResolvedForm, root: str, highlight: bool, classes: str = "") -> ui.element:
    """A Hebrew form, optionally coloured: root letters plain, inflection blue, pronominal suffix red."""
    if not highlight:
        return hebrew_text(resolved.form, classes)
    spans = "".join(
        f'<span class="{_SEGMENT_CLASSES[kind]}">{html.escape(part)}</span>'
        for kind, part in highlight_segments(resolved, root)
    )
    return ui.html(spans, sanitize=False, tag="span").classes(f"hebrew-text {classes}").props("lang=he dir=rtl")
