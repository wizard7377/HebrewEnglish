from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from hebrewenglish.gui.model import SUFFIX_OPTIONS, LexicalResult, SuffixId
from hebrewenglish.gui.theme import BORDER, SECTION_LABEL
from .elements import box, text
from .hebrew import hebrew_text
from .morphology import MorphologyDisplay, morphology_tabs


@dataclass
class EntryState:
    """Per-entry view state, kept across result refreshes."""

    expanded: bool
    tab: str
    suffix_id: SuffixId = SuffixId.NONE


def property_list(result: LexicalResult) -> None:
    with box():
        text("Inherent properties", f"mb-3 {SECTION_LABEL}", "h3")
        with box("grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-5", "dl"):
            for prop in result.properties:
                with box("min-w-0"):
                    text(prop.label, "text-[10px] font-semibold uppercase tracking-[0.1em] text-[#969187]", "dt")
                    if prop.hebrew:
                        hebrew_text(prop.value, "mt-1 block text-left text-lg leading-none text-[#303437]", "dd")
                    else:
                        text(prop.value, "mt-1 text-sm font-medium text-[#303437]", "dd")


def suffix_control(result: LexicalResult, value: SuffixId, on_change: Callable[[SuffixId], None]) -> None:
    """Choose a pronominal suffix to apply to every form of this entry; absent for parts of speech without one."""
    label = result.suffix_label
    if label is None:
        return
    with box(
        "flex flex-col gap-3 rounded border border-[#d8d8d8] bg-[#f7f9fb] p-4 "
        "sm:flex-row sm:items-center sm:justify-between"
    ):
        with box():
            text(label, "text-sm font-medium text-[#30343a]", "p")
            text(
                "Applies only to this lexical entry and updates forms and attestations.",
                "mt-1 text-xs leading-5 text-[#747b83]",
                "p",
            )
        ui.select(
            {option.id: option.label for option in SUFFIX_OPTIONS.values()},
            value=value,
            on_change=lambda e: on_change(SuffixId(e.value)),
        ).props(f'outlined dense bg-color=white aria-label="{label}"').classes("w-full sm:w-[290px]")


class LexicalAccordion:
    """One lexical possibility: a summary header that expands into properties, suffix choice and forms."""

    def __init__(self, result: LexicalResult, entry: EntryState, highlight: bool) -> None:
        self._result = result
        self._entry = entry
        self._highlight = highlight
        with ui.expansion(
            value=entry.expanded, on_value_change=lambda e: setattr(entry, "expanded", e.value)
        ).classes("ng-expansion w-full") as expansion:
            with expansion.add_slot("header"):
                self._header()
            self._details()

    def _header(self) -> None:
        result = self._result
        with box("flex w-full items-center gap-4 sm:gap-6"):
            with box("w-[76px] shrink-0"):
                text(
                    result.part_of_speech,
                    "block text-[10px] font-bold uppercase tracking-[0.14em] text-[#8b867d]",
                    "span",
                )
                if result.category_label:
                    text(
                        result.category_label,
                        "mt-2 inline-block rounded bg-[#e3f2fd] px-2 py-0.5 text-[9px] font-bold uppercase "
                        "tracking-[0.08em] text-[#27628f]",
                        "span",
                    )
            with box("w-[118px] shrink-0 sm:w-[150px]"):
                hebrew_text(
                    result.lemma, "block text-left text-[29px] leading-none text-[#202a30] sm:text-[34px]"
                )
                text(result.transliteration, "mt-1.5 block text-xs italic text-[#77746d]", "span")
            with box("min-w-0 flex-1"):
                text(
                    result.short_definition,
                    "block text-sm font-medium leading-6 text-[#424748] sm:text-[15px]",
                    "span",
                )
                text(
                    f"{len(result.morphology)} morphology groups",
                    # Quasar's .hidden is !important, so hide below sm rather than show above it
                    "mt-1 block text-[11px] text-[#928d83] max-sm:hidden",
                    "span",
                )

    @ui.refreshable_method
    def _details(self) -> None:
        result = self._result
        with box(f"w-full space-y-8 border-t border-[{BORDER}] px-5 py-7 sm:px-7 sm:py-8"):
            text(result.long_definition, "max-w-4xl text-base leading-7 text-[#4b5563]", "p")
            property_list(result)
            suffix_control(result, self._entry.suffix_id, self._set_suffix)
            box("h-px bg-[#e0dbd1]")
            morphology_tabs(
                MorphologyDisplay(result, self._entry.suffix_id, self._highlight),
                self._entry.tab,
                lambda tab: setattr(self._entry, "tab", tab),
            )

    def _set_suffix(self, suffix_id: SuffixId) -> None:
        self._entry.suffix_id = suffix_id
        self._details.refresh()
