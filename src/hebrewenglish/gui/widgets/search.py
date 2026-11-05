from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from hebrewenglish.gui.theme import BORDER, MUTED
from .elements import box, text


@dataclass
class SearchState:
    query: str = "guard"
    highlight: bool = False
    include_aramaic: bool = False
    include_proper_names: bool = False


class SearchCard:
    """The English search box, related-term shortcuts and result options."""

    def __init__(self, state: SearchState, on_change: Callable[[], None], related_terms: list[str]) -> None:
        self._state = state
        self._on_change = on_change
        with ui.card().tight().classes(f"ng-search-card mt-9 w-full rounded border border-[{BORDER}]"):
            with box("w-full p-4"):
                with box("flex flex-col gap-3 sm:flex-row"):
                    self._input = (
                        ui.input(placeholder="Enter an English word or phrase", value=state.query)
                        .props('outlined aria-label="English word or phrase"')
                        .classes("min-w-0 flex-1")
                        .on("keydown.enter", self._submit)
                        .on_value_change(lambda: self._message.set_visibility(False))
                    )
                    with self._input.add_slot("prepend"):
                        ui.icon("search").classes("text-[#8e8a80]")
                    ui.button("Find Hebrew", on_click=self._submit).classes(
                        "h-14 shrink-0 px-7 text-sm tracking-[0.06em]"
                    )
                self._message = text(
                    "Enter an English word to begin.", "px-2 pt-2 text-xs font-medium text-[#9b4b41]", "p"
                ).props("role=alert")
                self._message.set_visibility(False)
                with box(
                    f"mt-3 flex flex-col justify-between gap-2 border-t border-[{BORDER}] pt-3 "
                    "md:flex-row md:items-center"
                ):
                    with box(f"px-2 text-[11px] leading-5 text-[{MUTED}]", "p"):
                        text("Try a related term:", tag="span")
                        for term in related_terms:
                            text(
                                term,
                                "ml-2 cursor-pointer rounded font-semibold text-[#486c82] underline "
                                "decoration-[#9dafb9] underline-offset-2 hover:text-[#294f67]",
                                "button",
                            ).props("type=button").on("click", lambda term=term: self.search(term))
                    with box("flex flex-col gap-1 sm:flex-row sm:gap-4"):
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

        # Children of the switch fill its label slot, so clicking the text toggles it too
        with ui.switch(value=getattr(self._state, attribute), on_change=lambda e: changed(e.value)).classes(
            "ng-toggle min-h-11 rounded px-2 py-1.5"
        ):
            with box():
                text(label, "block text-[13px] font-medium leading-4 text-[#1d1d1d]", "span")
                text(hint, f"mt-0.5 block text-[11px] leading-4 text-[{MUTED}]", "span")
