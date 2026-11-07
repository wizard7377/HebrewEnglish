from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from .elements import caption


@dataclass
class SearchState:
    query: str = "guard"
    highlight: bool = False
    include_aramaic: bool = False
    include_proper_names: bool = False


@dataclass(frozen=True)
class SearchWording:
    """What the search box asks for, so one card serves both the English and the Hebrew search."""

    placeholder: str = "Enter an English word or phrase"
    label: str = "English word or phrase"
    button: str = "Find Hebrew"
    missing: str = "Enter an English word to begin."
    hebrew: bool = False


HEBREW_WORDING = SearchWording(
    placeholder="Enter a Hebrew word, with or without vowels",
    label="Hebrew word",
    button="Find English",
    missing="Enter a Hebrew word to begin.",
    hebrew=True,
)


class SearchCard:
    """The search box, related-term shortcuts and result options."""

    def __init__(
        self,
        state: SearchState,
        on_change: Callable[[], None],
        related_terms: list[str],
        wording: SearchWording = SearchWording(),
    ) -> None:
        self._state = state
        self._on_change = on_change
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center no-wrap"):
                self._input = (
                    ui.input(placeholder=wording.placeholder, value=state.query)
                    .props(f'outlined aria-label="{wording.label}"')
                    .classes("grow")
                    .on("keydown.enter", self._submit)
                    .on_value_change(lambda: self._message.set_visibility(False))
                )
                if wording.hebrew:
                    self._input.props("dir=rtl lang=he input-class=hebrew")
                with self._input.add_slot("prepend"):
                    ui.icon("search")
                ui.button(wording.button, on_click=self._submit).props("no-wrap")
            self._message = ui.label(wording.missing).classes("text-negative").props("role=alert")
            self._message.set_visibility(False)
            ui.separator()
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-1"):
                    caption("Try a related term:")
                    for term in related_terms:
                        button = ui.button(term, on_click=lambda term=term: self.search(term)).props("flat dense no-caps")
                        if wording.hebrew:
                            button.classes("hebrew text-body1")
                with ui.row().classes("gap-2"):
                    self._toggle("highlight", "Highlight morphology", "Inflection blue · suffix red")
                    self._toggle("include_aramaic", "Native Aramaic", "Include biblical Aramaic cognates")
                    self._toggle("include_proper_names", "Proper names", "Include related names")

    def search(self, query: str) -> None:
        self._input.value = query
        self._message.set_visibility(False)
        self._state.query = query
        self._on_change()

    def _submit(self) -> None:
        query = (self._input.value or "").strip()
        if not query:
            self._message.set_visibility(True)
            return
        self.search(query)

    def _toggle(self, attribute: str, label: str, hint: str) -> None:
        def changed(value: bool) -> None:
            setattr(self._state, attribute, value)
            self._on_change()

        ui.switch(label, value=getattr(self._state, attribute), on_change=lambda e: changed(e.value)).tooltip(hint)
