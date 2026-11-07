"""Colours and fonts for the Davar page; everything else is NiceGUI's and Quasar's own styling."""

from nicegui import ui

PRIMARY = "#5898d4"
# Quasar palette names for the parts of a highlighted form
INFLECTION = "blue-8"
SUFFIX = "red-8"

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Noto+Serif+Hebrew:wght@400;500&display=swap">'
)

# Quasar's fonts have no Hebrew points, so pointed text needs a font of its own
_CSS = """
.hebrew { font-family: "SBL Hebrew", "Noto Serif Hebrew", serif; unicode-bidi: isolate; }
"""


def apply_theme() -> None:
    """Install the Davar colours and Hebrew font on the current page."""
    ui.colors(primary=PRIMARY)
    ui.add_head_html(_FONTS)
    ui.add_css(_CSS)
    ui.query("body").classes("bg-white")
