from collections.abc import Callable

from nicegui import ui

from hebrewenglish.gui.model import Category, LexicalResult
from hebrewenglish.gui.theme import BORDER
from .attestation import attestation_legend
from .elements import box, text
from .lexical import EntryState, LexicalAccordion
from .search import SearchState

type Lookup = Callable[[str], list[LexicalResult]]


class ResultsSection:
    """The list of lexical possibilities for the current query, or an empty state."""

    def __init__(
        self, state: SearchState, lookup: Lookup, on_try: Callable[[str], None], related_terms: list[str]
    ) -> None:
        self._state = state
        self._lookup = lookup
        self._on_try = on_try
        self._related_terms = related_terms
        self._entries: dict[str, EntryState] = {}
        self.render()

    def _included(self, result: LexicalResult) -> bool:
        if result.category is Category.ARAMAIC:
            return self._state.include_aramaic
        if result.category is Category.PROPER_NAME:
            return self._state.include_proper_names
        return True

    def _entry(self, result: LexicalResult, first: bool) -> EntryState:
        # The most relevant result opens by default the first time it appears, on its most frequent stem
        if result.id not in self._entries:
            stem = result.stems[0] if result.stems else None
            groups = result.groups_for(stem)
            self._entries[result.id] = EntryState(expanded=first, tab=groups[0].id if groups else "", stem=stem)
        return self._entries[result.id]

    @ui.refreshable_method
    def render(self) -> None:
        query = self._state.query
        found = self._lookup(query)
        visible = [result for result in found if self._included(result)]

        with box(
            f"mb-5 flex flex-col gap-3 border-b border-[{BORDER}] pb-5 sm:flex-row sm:items-center sm:justify-between"
        ):
            with box():
                with box("text-sm font-semibold text-[#353a3c]", "p"):
                    count = len(visible)
                    text(f"{count} lexical {'possibility' if count == 1 else 'possibilities'}", tag="span")
                    if found:
                        text(f" for “{query}”", "font-normal text-[#8a867d]", "span")
                if found:
                    text("Ordered by semantic relevance", "mt-1 text-[11px] text-[#959087]", "p")
            attestation_legend()

        if not found:
            self._empty_state(query)
            return
        with box("w-full space-y-3"):
            for index, result in enumerate(visible):
                LexicalAccordion(result, self._entry(result, index == 0), self._state.highlight)

    def _empty_state(self, query: str) -> None:
        with box(f"rounded border border-[{BORDER}] bg-white px-6 py-14 text-center shadow-sm"):
            with box("mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#eee8db] text-[#786c52]"):
                ui.icon("search", size="20px")
            text(f"No entry for “{query}”", "mt-4 text-2xl text-[#30383c]", "h2")
            text(
                "Nothing in the lexicon matched this word. Try one of the English terms below.",
                "mx-auto mt-2 max-w-md text-sm leading-6 text-[#77736b]",
                "p",
            )
            with box("mt-5 flex justify-center gap-2"):
                for term in self._related_terms:
                    ui.button(term, on_click=lambda term=term: self._on_try(term)).props(
                        "outline rounded no-caps color=grey-8"
                    ).classes("min-h-10 px-4 text-xs font-semibold")
