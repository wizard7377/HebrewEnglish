from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from hebrewenglish.common.maybe import Maybe
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
    stem: Maybe[str] = None


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


def _option_control[T](label: str, hint: str, options: dict[T, str], value: T, on_change: Callable[[T], None]) -> None:
    with box(
        "flex flex-col gap-3 rounded border border-[#d8d8d8] bg-[#f7f9fb] p-4 "
        "sm:flex-row sm:items-center sm:justify-between"
    ):
        with box():
            text(label, "text-sm font-medium text-[#30343a]", "p")
            text(hint, "mt-1 text-xs leading-5 text-[#747b83]", "p")
        ui.select(options, value=value, on_change=lambda e: on_change(e.value)).props(
            f'outlined dense bg-color=white aria-label="{label}"'
        ).classes("w-full sm:w-[290px]")


def stem_control(result: LexicalResult, value: Maybe[str], on_change: Callable[[str], None]) -> None:
    """Choose which verbal stem's forms to show; absent for entries without stems."""
    if not result.stems:
        return
    _option_control(
        "Verbal stem",
        "The binyan whose conjugations are shown below, most frequent first.",
        {stem: stem for stem in result.stems},
        value,
        on_change,
    )


def suffix_control(result: LexicalResult, value: SuffixId, on_change: Callable[[SuffixId], None]) -> None:
    """Choose a pronominal suffix to apply to every form of this entry; absent for parts of speech without one."""
    label = result.suffix_label
    if label is None:
        return
    _option_control(
        label,
        "Applies only to this lexical entry and updates forms and attestations.",
        {option.id: option.label for option in SUFFIX_OPTIONS.values()},
        value,
        lambda suffix: on_change(SuffixId(suffix)),
    )


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
                stems, groups = len(result.stems), len(result.morphology)
                text(
                    f"{stems} stem{'s' if stems != 1 else ''}"
                    if stems
                    else f"{groups} morphology group{'s' if groups != 1 else ''}"
                    if groups
                    else "No forms recorded",
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
            stem_control(result, self._entry.stem, self._set_stem)
            suffix_control(result, self._entry.suffix_id, self._set_suffix)
            box("h-px bg-[#e0dbd1]")
            morphology_tabs(
                MorphologyDisplay(result, self._entry.suffix_id, self._highlight, self._entry.stem),
                self._entry.tab,
                lambda tab: setattr(self._entry, "tab", tab),
            )

    def _set_stem(self, stem: str) -> None:
        # Group ids are shared across stems, so the open tab carries over when the new stem has it
        self._entry.stem = stem
        self._details.refresh()

    def _set_suffix(self, suffix_id: SuffixId) -> None:
        self._entry.suffix_id = suffix_id
        self._details.refresh()
