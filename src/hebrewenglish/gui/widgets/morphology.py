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
from hebrewenglish.gui.theme import BORDER, COLUMN_LABEL, INFLECTION, SECTION_LABEL, SUFFIX
from .attestation import attestation_mark, reference_list
from .elements import box, text
from .hebrew import hebrew_text, highlighted_form

_TABLE = f"ng-table table-scroll relative w-full overflow-x-auto rounded border border-[{BORDER}] bg-white"
_HEAD = "border-b border-[#e0e0e0] bg-[#eee] text-[#555]"


@dataclass(frozen=True)
class MorphologyDisplay:
    """How one lexical entry's forms are shown: which suffix is applied and whether to colour morphemes."""

    result: LexicalResult
    suffix_id: SuffixId
    highlight: bool
    stem: Maybe[str] = None

    def resolve(self, row: MorphologyRow) -> Maybe[ResolvedForm]:
        return resolve_form(row, self.result, self.suffix_id)


def _no_form(display: MorphologyDisplay) -> None:
    text("—", "text-sm text-[#b0b0b0]", "span").props('aria-label="No form supplied"')
    if display.suffix_id is not SuffixId.NONE:
        text("No attested form with this suffix", "mt-1 block text-[10px] font-medium text-[#858585]", "span")


def morphology_form(row: MorphologyRow, display: MorphologyDisplay, show_evidence: bool = True) -> None:
    resolved = display.resolve(row)
    if resolved is None:
        with box("min-w-[132px]"):
            _no_form(display)
        return
    unattested = resolved.attestation is Attestation.UNATTESTED
    with box("min-w-[132px]"):
        highlighted_form(
            resolved,
            display.result.root,
            display.highlight,
            f"text-[24px] leading-tight {'text-[#77746d]' if unattested else 'text-[#202a30]'}",
        )
        if resolved.transliteration:
            text(
                resolved.transliteration,
                f"mt-1 block text-xs italic {'text-[#817e76]' if unattested else 'text-[#5d6263]'}",
                "span",
            )
        if display.suffix_id is SuffixId.NONE and row.alternative:
            with box("mt-1.5 flex items-baseline gap-2 text-[10px] uppercase tracking-[0.08em] text-[#969187]", "span"):
                text("also", tag="span")
                hebrew_text(row.alternative, "text-base normal-case tracking-normal text-[#676861]")
        if show_evidence:
            with box("mt-2"):
                attestation_mark(resolved.attestation, compact=True)
            reference_list(resolved)


def _paradigm_cell(row: Maybe[MorphologyRow], display: MorphologyDisplay, classes: str, merged: bool = False) -> None:
    resolved = display.resolve(row) if row is not None else None
    unattested = resolved is not None and resolved.attestation is Attestation.UNATTESTED
    cell = box(f"px-4 py-4 align-top {classes} {'unattested-row' if unattested else ''}", "td")
    if merged:
        cell.classes("ng-merged-cell").props("colspan=2")
    with cell:
        if row is None:
            text("—", "text-sm text-[#b0b0b0]", "span").props('aria-label="No form supplied"')
            return
        if resolved is None:
            _no_form(display)
            return
        if merged:
            text(
                "Common gender",
                "mb-2 inline-flex rounded bg-[#e3f2fd] px-1.5 py-0.5 text-[9px] font-medium uppercase "
                "tracking-[0.08em] text-[#27628f]",
                "span",
            )
        morphology_form(row, display)


def conjugation_table(group: MorphologyGroup, display: MorphologyDisplay) -> None:
    """Verb paradigm: person down the side, singular/plural × masculine/feminine across."""
    participle = "participle" in group.id
    with box(_TABLE):
        with box("w-full min-w-[920px] border-collapse text-left", "table"):
            with box(tag="thead"):
                with box(_HEAD, "tr"):
                    text(
                        "Form" if participle else "Person",
                        f"sticky left-0 z-20 w-28 border-r bg-[#eee] px-4 py-3 {COLUMN_LABEL}",
                        "th",
                    ).props("scope=col rowspan=2")
                    text("Singular", f"border-r px-4 py-2 text-center {COLUMN_LABEL}", "th").props(
                        "scope=colgroup colspan=2"
                    )
                    text("Plural", f"px-4 py-2 text-center {COLUMN_LABEL}", "th").props("scope=colgroup colspan=2")
                with box(_HEAD, "tr"):
                    for index, (_, label) in enumerate(PARADIGM_COLUMNS):
                        text(
                            label,
                            f"min-w-[195px] px-4 py-2 text-[10px] font-bold uppercase tracking-[0.1em] "
                            f"{'border-r' if index == 1 else ''}",
                            "th",
                        ).props("scope=col")
            with box(tag="tbody"):
                for person in paradigm_people(group):
                    with box("border-b border-[#e0e0e0] last:border-0", "tr"):
                        text(
                            person,
                            "ng-person-cell sticky left-0 z-10 border-r bg-[#f5f5f5] px-4 py-5 align-top "
                            "text-sm font-medium text-[#444]",
                            "th",
                        ).props("scope=row")
                        # Singular pair, then plural pair; identical masc/fem forms merge into one common-gender cell
                        for pair, edge in [(PARADIGM_COLUMNS[:2], "border-r"), (PARADIGM_COLUMNS[2:], "")]:
                            first, second = (paradigm_row(group, person, slot) for slot, _ in pair)
                            if first and second:
                                a, b = display.resolve(first), display.resolve(second)
                                if a and b and a.form == b.form and a.attestation is b.attestation:
                                    _paradigm_cell(first, display, edge, merged=True)
                                    continue
                            _paradigm_cell(first, display, "")
                            _paradigm_cell(second, display, edge)


def forms_table(group: MorphologyGroup, display: MorphologyDisplay) -> None:
    """One row per form, for parts of speech without a person paradigm."""
    head = f"px-5 py-3 {COLUMN_LABEL} text-[#555]"
    # Real forms carry no transliteration of their own, only the lemma does
    transliterated = any(row.transliteration for row in group.rows)
    with box(_TABLE):
        with box("w-full min-w-[680px] border-collapse text-left", "table"):
            with box(tag="thead"):
                with box(_HEAD, "tr"):
                    text("Form", f"sticky left-0 z-10 w-40 bg-[#eee] {head}", "th").props("scope=col")
                    text("Biblical Hebrew", head, "th").props("scope=col")
                    if transliterated:
                        text("Transliteration", head, "th").props("scope=col")
                    text("Evidence", f"w-36 {head}", "th").props("scope=col")
            with box(tag="tbody"):
                for row in group.rows:
                    resolved = display.resolve(row)
                    unattested = resolved is None or resolved.attestation is Attestation.UNATTESTED
                    with box(
                        f"border-b border-[#e5e1d8] last:border-b-0 {'unattested-row' if unattested else 'bg-white'}",
                        "tr",
                    ):
                        with box(
                            "sticky left-0 z-[1] px-5 py-4 align-middle text-sm font-semibold "
                            + ("unattested-sticky text-[#77746d]" if unattested else "bg-white text-[#303437]"),
                            "th",
                        ).props("scope=row"):
                            text(row.label, tag="span")
                            if row.note:
                                text(row.note, "mt-0.5 block text-[11px] font-normal text-[#8b877e]", "span")
                        with box("px-5 py-3.5 align-middle", "td"):
                            morphology_form(row, display, show_evidence=False)
                        if transliterated:
                            text(
                                resolved.transliteration if resolved else "",
                                f"px-5 py-4 text-sm italic {'text-[#817e76]' if unattested else 'text-[#5d6263]'}",
                                "td",
                            )
                        with box("px-5 py-4", "td"):
                            if resolved is not None:
                                attestation_mark(resolved.attestation)
                                reference_list(resolved)


def morphology_tabs(display: MorphologyDisplay, active_tab: str, on_tab_change: Callable[[str], None]) -> None:
    """Tabs over a lexical entry's morphology groups, each showing its table of forms."""
    result = display.result
    groups = {group.id: group for group in result.groups_for(display.stem)}
    if not groups:
        with box("w-full"):
            text("Morphological forms", SECTION_LABEL, "h3")
            text("No morphology recorded for this entry.", "mt-2 text-sm text-[#8a867d]", "p")
        return
    active = groups.get(active_tab, next(iter(groups.values())))

    def changed(tab: str) -> None:
        description.set_text(groups[tab].description)
        on_tab_change(tab)

    with box("w-full"):
        with box("mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"):
            with box():
                text("Morphological forms", SECTION_LABEL, "h3")
                description = text(active.description, "mt-1 text-xs text-[#8a867d]", "p")
            with box("flex flex-wrap items-center gap-3 text-[10px] uppercase tracking-[0.08em] text-[#9a958b]"):
                text("Pointed Masoretic forms", tag="span")
                if display.highlight:
                    for colour, label in [(INFLECTION, "Inflection"), (SUFFIX, "Object / possessive suffix")]:
                        with box("inline-flex items-center gap-1.5", "span"):
                            box(f"h-2 w-2 rounded-full bg-[{colour}]", "span")
                            text(label, tag="span")
        with ui.tabs(value=active.id, on_change=lambda e: changed(e.value)).props(
            "align=left active-color=primary indicator-color=primary"
        ).classes(f"ng-tabs mb-3 w-full border-b border-[{BORDER}]") as tabs:
            for group in groups.values():
                ui.tab(group.id, label=group.label)
        with ui.tab_panels(tabs, value=active.id, animated=False).classes("w-full bg-transparent"):
            for group in groups.values():
                with ui.tab_panel(group.id).style("padding: 0"):
                    # Infinitives have no person or gender, so they list like other forms
                    if result.part_of_speech == "Verb" and "infinitive" not in group.id:
                        conjugation_table(group, display)
                    else:
                        forms_table(group, display)
