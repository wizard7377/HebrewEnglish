"""The Davar page: an English → Hebrew reverse lexicon and a Hebrew → English lexicon, with a tab for the
Hebrew → Hebrew tool to come."""

from dataclasses import dataclass
from functools import cache

from nicegui import ui

from hebrewenglish.backend.logic import Backend
from hebrewenglish.gui import demo
from hebrewenglish.gui.adapter import make_hebrew_lookup, make_lookup
from hebrewenglish.gui.theme import apply_theme
from hebrewenglish.gui.widgets.elements import caption
from hebrewenglish.gui.widgets.results import Lookup, ResultsSection
from hebrewenglish.gui.widgets.search import HEBREW_WORDING, SearchCard, SearchState, SearchWording


# The page's tools, by tab id and label; Hebrew → Hebrew is not built yet
TOOLS = {
    "english-hebrew": "English → Hebrew",
    "hebrew-hebrew": "Hebrew → Hebrew",
    "hebrew-english": "Hebrew → English",
}


def _header() -> ui.tabs:
    with ui.header(elevated=True).classes("items-center"):
        ui.icon("menu_book", size="sm")
        with ui.column().classes("gap-0"):
            ui.label("Davar").classes("text-h6")
            ui.label("Biblical Hebrew Lexicon").classes("text-overline")
        with ui.tabs(value=next(iter(TOOLS))).props("inline-label outside-arrows mobile-arrows").classes("min-w-0") as tabs:
            for tool, label in TOOLS.items():
                ui.tab(tool, label=label)
    return tabs


def _footer() -> None:
    ui.separator()
    with ui.row().classes("w-full justify-between"):
        caption("Strong's Hebrew Dictionary · Morphology: Open Scriptures Hebrew Bible (WLC), CC BY 4.0")
        caption("Hebrew typography: SBL Hebrew / Noto Serif Hebrew")


@dataclass(frozen=True)
class _Tool:
    """The wording of one lookup tab."""

    overline: str
    title: str
    blurb: str
    query: str
    related_terms: list[str]
    ordering: str
    wording: SearchWording = SearchWording()


_ENGLISH_HEBREW = _Tool(
    "English → Biblical Hebrew",
    "Find the Hebrew behind an English word",
    "Explore lexical nuance, inherent grammar, and attested forms across the Hebrew Bible.",
    "guard",
    demo.RELATED_TERMS,
    "Ordered by semantic relevance",
)
_HEBREW_ENGLISH = _Tool(
    "Biblical Hebrew → English",
    "Find the meaning of a Hebrew word",
    "Type any form as it stands in the text, prefixes and all; the lemmas spelled like it and their relatives "
    "come back with their definitions and forms.",
    "שמר",
    demo.HEBREW_TERMS,
    "Ordered by Hebrew spelling: the word itself, then its root, then near spellings",
    HEBREW_WORDING,
)


def _dictionary(tool: _Tool, lookup: Lookup) -> None:
    state = SearchState(query=tool.query)
    with ui.column().classes("w-full max-w-5xl mx-auto"):
        with ui.column().classes("w-full items-center text-center gap-2"):
            ui.label(tool.overline).classes("text-overline text-primary")
            ui.label(tool.title).classes("text-h4")
            caption(tool.blurb)
        search = SearchCard(state, lambda: results.render.refresh(), tool.related_terms, tool.wording)
        results = ResultsSection(
            state, lookup, search.search, tool.related_terms, tool.ordering, tool.wording.hebrew
        )
        _footer()


def build_page(lookup: Lookup, hebrew_lookup: Lookup) -> None:
    apply_theme()
    tabs = _header()
    with ui.tab_panels(tabs, value=next(iter(TOOLS)), animated=False).classes("w-full"):
        with ui.tab_panel("english-hebrew"):
            _dictionary(_ENGLISH_HEBREW, lookup)
        # Left blank until its tool is built
        ui.tab_panel("hebrew-hebrew")
        with ui.tab_panel("hebrew-english"):
            _dictionary(_HEBREW_ENGLISH, hebrew_lookup)


@cache
def _backend() -> Backend:
    # Built on the first visit, so importing the page does not wait for the lexicon
    return Backend()


@cache
def _lexicon_lookups() -> tuple[Lookup, Lookup]:
    return make_lookup(_backend()), make_hebrew_lookup(_backend())


def davar_page() -> None:
    """Page entry point, served from the real lexicon and morphology."""
    build_page(*_lexicon_lookups())


def demo_page() -> None:
    """The same page over the hand-written demonstration entries."""
    build_page(demo.lookup, demo.hebrew_lookup)
