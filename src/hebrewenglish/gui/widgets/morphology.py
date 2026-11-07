from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.gui.model import (
    PARADIGM_COLUMNS,
    Attestation,
    LexicalResult,
    MorphologyGroup,
    MorphologyRow,
    ResolvedForm,
    SuffixId,
    paradigm_people,
    paradigm_row,
    resolve_form,
)
from hebrewenglish.gui.theme import INFLECTION, SUFFIX

from .attestation import attestation_badge, reference_list
from .elements import caption, heading
from .hebrew import hebrew_text, highlighted_form

# Tables scroll sideways rather than squeeze their Hebrew below this width per column
_COLUMN = "minmax(9rem, 1fr)"


@dataclass(frozen=True)
class MorphologyDisplay:
    """How one lexical entry's forms are shown: which suffix is applied and whether to colour morphemes."""

    result: LexicalResult
    suffix_id: SuffixId
    highlight: bool
    stem: Maybe[str] = None

    def resolve(self, row: MorphologyRow) -> Maybe[ResolvedForm]:
        return resolve_form(row, self.result, self.suffix_id)


def _unattested(resolved: Maybe[ResolvedForm]) -> bool:
    return resolved is None or resolved.attestation is Attestation.UNATTESTED


def _cell(shaded: bool = False, span: int = 1) -> ui.column:
    """One grid cell; unattested forms are shaded grey."""
    return ui.column().classes(f"gap-1 p-2 rounded-borders {'bg-grey-2' if shaded else ''} col-span-{span}")


def _column_label(label: str) -> None:
    ui.label(label).classes("text-overline text-grey-8 p-2")


def _table(columns: str) -> ui.grid:
    with ui.element().classes("w-full overflow-x-auto"):
        return ui.grid(columns=columns).classes("w-full items-start gap-x-2 gap-y-1")


def _no_form(display: MorphologyDisplay) -> None:
    ui.label("—").classes("text-grey").props('aria-label="No form supplied"')
    if display.suffix_id is not SuffixId.NONE:
        caption("No attested form with this suffix")


def morphology_form(row: MorphologyRow, display: MorphologyDisplay, show_evidence: bool = True) -> None:
    resolved = display.resolve(row)
    if resolved is None:
        _no_form(display)
        return
    unattested = _unattested(resolved)
    highlighted_form(
        resolved, display.result.root, display.highlight, f"text-h5 {'text-grey-7' if unattested else ''}"
    )
    if resolved.transliteration:
        ui.label(resolved.transliteration).classes("text-caption text-italic text-grey-7")
    if display.suffix_id is SuffixId.NONE and row.alternative:
        with ui.row().classes("items-center gap-2"):
            caption("also")
            hebrew_text(row.alternative, "text-subtitle1 text-grey-8")
    if show_evidence:
        attestation_badge(resolved.attestation)
        reference_list(resolved)


def _paradigm_cell(row: Maybe[MorphologyRow], display: MorphologyDisplay, merged: bool = False) -> None:
    resolved = display.resolve(row) if row is not None else None
    with _cell(shaded=row is not None and _unattested(resolved), span=2 if merged else 1):
        if row is None:
            ui.label("—").classes("text-grey").props('aria-label="No form supplied"')
            return
        if merged and resolved is not None:
            ui.badge("Common gender").props("outline")
        morphology_form(row, display)


def conjugation_table(group: MorphologyGroup, display: MorphologyDisplay) -> None:
    """Verb paradigm: person down the side, singular/plural × masculine/feminine across."""
    with _table(f"auto repeat(4, {_COLUMN})"):
        _column_label("Form" if "participle" in group.id else "Person")
        for index, (_, gender) in enumerate(PARADIGM_COLUMNS):
            _column_label(f"{gender} {'singular' if index < 2 else 'plural'}")
        for person in paradigm_people(group):
            ui.separator().classes("col-span-full")
            ui.label(person).classes("text-subtitle2 p-2")
            # Singular pair, then plural pair; identical masc/fem forms merge into one common-gender cell
            for pair in (PARADIGM_COLUMNS[:2], PARADIGM_COLUMNS[2:]):
                first, second = (paradigm_row(group, person, slot) for slot, _ in pair)
                if first and second:
                    a, b = display.resolve(first), display.resolve(second)
                    if a and b and a.form == b.form and a.attestation is b.attestation:
                        _paradigm_cell(first, display, merged=True)
                        continue
                _paradigm_cell(first, display)
                _paradigm_cell(second, display)


def forms_table(group: MorphologyGroup, display: MorphologyDisplay) -> None:
    """One row per form, for parts of speech without a person paradigm."""
    # Real forms carry no transliteration of their own, only the lemma does
    transliterated = any(row.transliteration for row in group.rows)
    columns = ["Form", "Biblical Hebrew", *(["Transliteration"] if transliterated else []), "Evidence"]
    with _table(f"auto repeat({len(columns) - 1}, {_COLUMN})"):
        for label in columns:
            _column_label(label)
        for row in group.rows:
            resolved = display.resolve(row)
            unattested = _unattested(resolved)
            ui.separator().classes("col-span-full")
            with _cell(unattested):
                ui.label(row.label).classes("text-subtitle2")
                if row.note:
                    caption(row.note)
            with _cell(unattested):
                morphology_form(row, display, show_evidence=False)
            if transliterated:
                with _cell(unattested):
                    ui.label(resolved.transliteration if resolved else "").classes("text-italic text-grey-8")
            with _cell(unattested):
                if resolved is not None:
                    attestation_badge(resolved.attestation)
                    reference_list(resolved)


def morphology_tabs(display: MorphologyDisplay, active_tab: str, on_tab_change: Callable[[str], None]) -> None:
    """Tabs over a lexical entry's morphology groups, each showing its table of forms."""
    result = display.result
    groups = {group.id: group for group in result.groups_for(display.stem)}
    if not groups:
        heading("Morphological forms")
        caption("No morphology recorded for this entry.")
        return
    active = groups.get(active_tab, next(iter(groups.values())))

    def changed(tab: str) -> None:
        description.set_text(groups[tab].description)
        on_tab_change(tab)

    with ui.row().classes("w-full items-end justify-between"):
        with ui.column().classes("gap-0"):
            heading("Morphological forms")
            description = caption(active.description)
        with ui.row().classes("items-center gap-2"):
            caption("Pointed Masoretic forms")
            if display.highlight:
                ui.badge("Inflection", color=INFLECTION)
                ui.badge("Object / possessive suffix", color=SUFFIX)
    with ui.tabs(value=active.id, on_change=lambda e: changed(e.value)).props(
        "align=left active-color=primary indicator-color=primary"
    ).classes("w-full") as tabs:
        for group in groups.values():
            ui.tab(group.id, label=group.label)
    with ui.tab_panels(tabs, value=active.id, animated=False).classes("w-full"):
        for group in groups.values():
            with ui.tab_panel(group.id):
                # Infinitives have no person or gender, so they list like other forms
                if result.part_of_speech == "Verb" and "infinitive" not in group.id:
                    conjugation_table(group, display)
                else:
                    forms_table(group, display)
