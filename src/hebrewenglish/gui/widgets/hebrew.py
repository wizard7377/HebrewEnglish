import html

from nicegui import ui

from hebrewenglish.gui.model import ResolvedForm, highlight_segments
from hebrewenglish.gui.theme import INFLECTION, SUFFIX

_SEGMENT_CLASSES = {
    "root": "",
    "inflection": f"text-{INFLECTION}",
    "suffix": f"text-{SUFFIX}",
}


def hebrew_text(value: str, classes: str = "") -> ui.label:
    """Right-to-left text in the pointed Hebrew font."""
    return ui.label(value).classes(f"hebrew {classes}").props("lang=he dir=rtl")


def highlighted_form(
    resolved: ResolvedForm, root: str, highlight: bool, classes: str = ""
) -> ui.element:
    """A Hebrew form, optionally coloured: root letters plain, inflection blue, pronominal suffix red."""
    if not highlight:
        return hebrew_text(resolved.form, classes)
    spans = "".join(
        f'<span class="{_SEGMENT_CLASSES[kind]}">{html.escape(part)}</span>'
        for kind, part in highlight_segments(resolved, root)
    )
    return ui.html(spans, sanitize=False).classes(f"hebrew {classes}").props("lang=he dir=rtl")
