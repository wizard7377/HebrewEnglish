from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.gui.model import SUFFIX_OPTIONS, LexicalResult, SuffixId

from .definitions import SefariaDefinitions, definitions, stem_definitions
from .elements import caption, heading
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
    heading("Inherent properties")
    with ui.row().classes("w-full gap-x-8"):
        for prop in result.properties:
            with ui.column().classes("gap-0"):
                caption(prop.label)
                if prop.hebrew:
                    hebrew_text(prop.value, "text-h6")
                else:
                    ui.label(prop.value).classes("text-body2")


def _option_control[T](
    label: str,
    hint: str,
    options: dict[T, str],
    value: T,
    on_change: Callable[[T], None],
) -> None:
    ui.select(options, label=label, value=value, on_change=lambda e: on_change(e.value)).props(
        f'outlined dense hint="{hint}"'
    ).classes("w-full max-w-sm")


def stem_control(
    result: LexicalResult, value: Maybe[str], on_change: Callable[[str], None]
) -> None:
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


def suffix_control(
    result: LexicalResult, value: SuffixId, on_change: Callable[[SuffixId], None]
) -> None:
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

    def __init__(
        self, result: LexicalResult, entry: EntryState, highlight: bool
    ) -> None:
        self._result = result
        self._entry = entry
        self._highlight = highlight
        self._sefaria = SefariaDefinitions(result, self._definitions_loaded)
        with ui.card().tight().classes("w-full"):
            with ui.expansion(
                value=entry.expanded,
                on_value_change=lambda e: setattr(entry, "expanded", e.value),
            ).classes("w-full") as expansion:
                with expansion.add_slot("header"):
                    self._header()
                self._details()
        self._expansion = expansion

    def _header(self) -> None:
        result = self._result
        # The gloss drops below the lemma when a phone leaves it too little room
        with ui.row().classes("w-full items-center py-2"):
            with ui.column().classes("w-20 shrink-0 gap-1"):
                ui.label(result.part_of_speech).classes("text-overline text-grey-7")
                if result.category_label:
                    ui.badge(result.category_label).props("outline")
            with ui.column().classes("w-36 shrink-0 gap-0"):
                hebrew_text(result.lemma, "text-h4")
                ui.label(result.transliteration).classes("text-caption text-italic text-grey-7")
            with ui.column().classes("min-w-40 flex-1 gap-0"):
                ui.label(result.short_definition).classes("text-subtitle1")
                if result.occurrences is not None:
                    caption(f"{result.occurrences:,} occurrence{'s' if result.occurrences != 1 else ''}")
                stems, groups = len(result.stems), len(result.morphology)
                summary = (
                    f"{stems} stem{'s' if stems != 1 else ''}"
                    if stems
                    else f"{groups} morphology group{'s' if groups != 1 else ''}"
                    if groups
                    else "No forms recorded"
                )
                caption(summary).classes("gt-xs")

    @ui.refreshable_method
    def _details(self) -> None:
        result = self._result
        ui.separator()
        ui.label(result.long_definition).classes("text-body1")
        definitions(self._sefaria)
        property_list(result)
        stem_control(result, self._entry.stem, self._set_stem)
        stem_definitions(self._sefaria, self._entry.stem)
        suffix_control(result, self._entry.suffix_id, self._set_suffix)
        ui.separator()
        morphology_tabs(
            MorphologyDisplay(result, self._entry.suffix_id, self._highlight, self._entry.stem),
            self._entry.tab,
            lambda tab: setattr(self._entry, "tab", tab),
        )

    def _definitions_loaded(self) -> None:
        # The results may have been redrawn, or the visitor gone, while Sefaria answered
        if not self._expansion.is_deleted:
            self._details.refresh()

    def _set_stem(self, stem: str) -> None:
        # Group ids are shared across stems, so the open tab carries over when the new stem has it
        self._entry.stem = stem
        self._details.refresh()

    def _set_suffix(self, suffix_id: SuffixId) -> None:
        self._entry.suffix_id = suffix_id
        self._details.refresh()
