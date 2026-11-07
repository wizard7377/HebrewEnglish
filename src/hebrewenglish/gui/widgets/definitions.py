"""Definitions from Sefaria's lexicon, fetched in the background so the page never waits on the network."""

from collections.abc import Callable

from nicegui import background_tasks, run, ui
import requests

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.gui.model import Attestation, LexicalResult
from hebrewenglish.lexicon.sefaria import SefariaLexicon, Sense, lookup

from .elements import caption, heading

# Fetched entries by lemma and Strong's number, shared by every visitor; a failed fetch is left out to be retried
_fetched: dict[tuple[str, str], Maybe[SefariaLexicon]] = {}


def _attestations(result: LexicalResult, limit: int = 3) -> tuple[tuple[str, str], ...]:
    """A few attested forms, each with a verse it is found in, for when Sefaria does not know the lemma."""
    forms = [row for group in result.morphology for row in group.rows] + list(result.suffixed_forms.values())
    found = dict.fromkeys(
        (form.form, form.references[0])
        for form in forms
        if form.attestation is Attestation.ATTESTED and form.form and form.references
    )
    return tuple(found)[:limit]


class SefariaDefinitions:
    """One result's Sefaria entry, loaded in the background; ``on_loaded`` redraws whatever shows it."""

    def __init__(self, result: LexicalResult, on_loaded: Callable[[], None]) -> None:
        self._key = (result.lemma, result.strong_number) if result.strong_number else None
        self._attestations = _attestations(result)
        self.failed = False
        if self._key is not None and self._key not in _fetched:
            background_tasks.create(self._load(on_loaded))

    @property
    def available(self) -> bool:
        return self._key is not None

    @property
    def loading(self) -> bool:
        return self._key is not None and self._key not in _fetched and not self.failed

    @property
    def entry(self) -> Maybe[SefariaLexicon]:
        return _fetched.get(self._key) if self._key is not None else None

    async def _load(self, on_loaded: Callable[[], None]) -> None:
        assert self._key is not None
        try:
            _fetched[self._key] = await run.io_bound(lookup, *self._key, self._attestations)
        except requests.RequestException:
            self.failed = True
        on_loaded()


def _sense_list(senses: tuple[Sense, ...], depth: int = 0) -> None:
    with ui.element("ol").classes(f"{'list-decimal' if depth == 0 else 'list-disc'} pl-6 space-y-1"):
        for sense in senses:
            with ui.element("li"):
                ui.label(sense.definition).classes("text-body2")
                if sense.senses:
                    _sense_list(sense.senses, depth + 1)


def _heading(title: str) -> None:
    with ui.row().classes("w-full items-baseline justify-between"):
        heading(title)
        caption("BDB · Sefaria")


def definitions(sefaria: SefariaDefinitions) -> None:
    """The senses of the word as a whole, or why there are none to show."""
    if not sefaria.available:
        return
    with ui.column().classes("w-full gap-1"):
        _heading("Definitions")
        entry = sefaria.entry
        if sefaria.loading:
            with ui.row().classes("items-center gap-2"):
                ui.spinner()
                caption("Loading definitions from Sefaria…")
        elif sefaria.failed:
            caption("Sefaria could not be reached.")
        elif entry is None or not (entry.senses or entry.stems):
            caption("Sefaria has no entry for this word.")
        elif entry.senses:
            _sense_list(entry.senses)
        else:
            caption("Sefaria defines this word by stem only; choose a stem below.")


def stem_definitions(sefaria: SefariaDefinitions, stem: Maybe[str]) -> None:
    """The senses of one verbal stem, when Sefaria gives that stem any."""
    entry = sefaria.entry
    if stem is None or entry is None or stem not in entry.stems:
        return
    with ui.column().classes("w-full gap-1"):
        _heading(f"{stem} meanings")
        _sense_list(entry.stems[stem])
