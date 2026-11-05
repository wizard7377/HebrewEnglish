"""The Davar reverse-lexicon page: English word in, Biblical Hebrew lexical possibilities out."""

from nicegui import ui

from hebrewenglish.gui import demo
from hebrewenglish.gui.theme import BORDER, HERO, PRIMARY_DARK, apply_theme
from hebrewenglish.gui.widgets.elements import box, text
from hebrewenglish.gui.widgets.results import Lookup, ResultsSection
from hebrewenglish.gui.widgets.search import SearchCard, SearchState


def _header() -> None:
    with ui.header(elevated=True).classes("bg-primary text-white").style("padding: 0"):
        with box("mx-auto flex h-16 w-full max-w-[1180px] items-center justify-between px-5 sm:px-8"):
            with box("flex items-center gap-3"):
                with box("flex h-9 w-9 items-center justify-center rounded-full bg-white/15"):
                    ui.icon("menu_book", size="19px")
                with box():
                    text("Davar", "block text-xl font-semibold leading-5 tracking-[-0.01em]", "span")
                    text("Biblical Hebrew Lexicon", "block text-[9px] font-semibold uppercase tracking-[0.16em]", "span")
            text("Reverse lexicon · Prototype", "text-[11px] font-semibold uppercase tracking-[0.14em] max-sm:hidden", "span")


def _footer() -> None:
    with box(
        f"mt-10 flex flex-col gap-2 border-t border-[{BORDER}] pt-5 text-[10px] uppercase tracking-[0.11em] "
        "text-[#98938a] sm:flex-row sm:items-center sm:justify-between",
        "footer",
    ):
        text("Prototype lexical data · Forms shown for interface demonstration", tag="p")
        text("Hebrew typography: SBL Hebrew / Noto Serif Hebrew", tag="p")


def build_page(lookup: Lookup) -> None:
    apply_theme()
    state = SearchState()
    _header()
    with box(f"w-full border-b border-[{BORDER}] bg-[{HERO}] px-5 pb-9 pt-12 sm:px-8 sm:pb-12 sm:pt-16", "section"):
        with box("mx-auto max-w-[980px]"):
            with box("mx-auto max-w-3xl text-center"):
                text(
                    "English → Biblical Hebrew",
                    f"mb-3 text-[10px] font-bold uppercase tracking-[0.19em] text-[{PRIMARY_DARK}]",
                    "p",
                )
                text(
                    "Find the Hebrew behind an English word",
                    "text-[36px] font-normal leading-[1.08] tracking-[-0.02em] text-[#202124] sm:text-[52px]",
                    "h1",
                )
                text(
                    "Explore lexical nuance, inherent grammar, and attested forms across the Hebrew Bible.",
                    "mx-auto mt-4 max-w-2xl text-sm leading-6 text-[#706e68] sm:text-[15px]",
                    "p",
                )
            search = SearchCard(state, lambda: results.render.refresh(), demo.RELATED_TERMS)
    with box("w-full px-5 py-8 sm:px-8 sm:py-10", "section"):
        with box("mx-auto max-w-[1080px]"):
            results = ResultsSection(state, lookup, search.search, demo.RELATED_TERMS)
            _footer()


def davar_page() -> None:
    """Page entry point, served with the demonstration lexicon until the backend supplies results."""
    build_page(demo.lookup)
