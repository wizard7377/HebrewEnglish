from collections.abc import Callable

from nicegui import ui

from hebrewenglish.gui.model import Category, LexicalResult

from .attestation import attestation_legend
from .elements import caption
from .lexical import EntryState, LexicalAccordion
from .search import SearchState

type Lookup = Callable[[str], list[LexicalResult]]


class ResultsSection:
    """The list of lexical possibilities for the current query, or an empty state."""

    def __init__(
        self,
        state: SearchState,
        lookup: Lookup,
        on_try: Callable[[str], None],
        related_terms: list[str],
        ordering: str = "Ordered by semantic relevance",
        hebrew: bool = False,
    ) -> None:
        self._state = state
        self._ordering = ordering
        self._hebrew = hebrew
        self._lookup = lookup
        self._on_try = on_try
        self._related_terms = related_terms
        self._entries: dict[str, EntryState] = {}
        with ui.column().classes("w-full items-stretch"):
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
            self._entries[result.id] = EntryState(
                expanded=first, tab=groups[0].id if groups else "", stem=stem
            )
        return self._entries[result.id]

    @ui.refreshable_method
    def render(self) -> None:
        query = self._state.query
        found = self._lookup(query)
        visible = [result for result in found if self._included(result)]

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                count = len(visible)
                title = f"{count} lexical {'possibility' if count == 1 else 'possibilities'}"
                ui.label(f"{title} for “{query}”" if found else title).classes("text-subtitle1")
                if found:
                    caption(self._ordering)
            attestation_legend()

        if not found:
            self._empty_state(query)
            return
        for index, result in enumerate(visible):
            LexicalAccordion(result, self._entry(result, index == 0), self._state.highlight)

    def _empty_state(self, query: str) -> None:
        with ui.card().classes("w-full items-center"):
            ui.icon("search", size="lg", color="grey")
            ui.label(f"No entry for “{query}”").classes("text-h5")
            caption("Nothing in the lexicon matched this word. Try one of the terms below.")
            with ui.row():
                for term in self._related_terms:
                    button = ui.button(term, on_click=lambda term=term: self._on_try(term)).props("outline no-caps")
                    if self._hebrew:
                        button.classes("hebrew")
