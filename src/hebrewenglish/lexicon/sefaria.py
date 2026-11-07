"""Definitions from Sefaria's lexicon API (``https://www.sefaria.org/api/words/<word>``), split by verbal stem."""

import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import itertools
from typing import Any
import unicodedata

import requests

from hebrewenglish.common.maybe import Maybe

_API = "https://www.sefaria.org/api/words/"
_TEXTS = "https://www.sefaria.org/api/v3/texts/"
_TIMEOUT = 10
# Sefaria's spelling of a stem, where it differs from the OSHB name the page shows
_STEM_NAMES = {"P'al": "Peal"}


class Dictionary(Enum):
    """A Sefaria lexicon, by the name its API gives it."""

    # BDB abridged and keyed by Strong's number, with each sense tagged by its verbal stem
    STRONG = "BDB Augmented Strong"


@dataclass(frozen=True)
class Sense:
    definition: str
    senses: tuple["Sense", ...] = ()


@dataclass(frozen=True)
class SefariaLexicon:
    """One Sefaria entry: the senses of the word as a whole, and those that belong to one verbal stem."""

    headword: str
    senses: tuple[Sense, ...]
    stems: dict[str, tuple[Sense, ...]] = field(default_factory=dict)


def _clean(definition: str) -> str:
    return re.sub(r"\s+", " ", definition).strip()


def parse_senses(raw: list[dict[str, Any]], stems: dict[str, tuple[Sense, ...]]) -> tuple[Sense, ...]:
    """The senses of an API sense tree; a subtree tagged with a verbal stem goes into ``stems`` instead."""
    senses: list[Sense] = []
    for node in raw:
        children = parse_senses(node.get("senses", []), stems)
        definition = _clean(node.get("definition", ""))
        # A node without a definition only groups its children
        own = (Sense(definition, children),) if definition else children
        stem = (node.get("grammar") or {}).get("verbal_stem")
        if stem:
            stem = _STEM_NAMES.get(stem, stem)
            stems[stem] = stems.get(stem, ()) + own
        else:
            senses.extend(own)
    return tuple(senses)


def find_entry(
    entries: list[dict[str, Any]], strong_number: str, dictionary: Dictionary = Dictionary.STRONG
) -> Maybe[SefariaLexicon]:
    """The entry with this Strong's number among the API's results for a word."""
    for entry in entries:
        if entry.get("parent_lexicon") == dictionary.value and entry.get("strong_number") == strong_number:
            stems: dict[str, tuple[Sense, ...]] = {}
            senses = parse_senses(entry.get("content", {}).get("senses", []), stems)
            return SefariaLexicon(entry.get("headword", ""), senses, stems)
    return None


def _consonants(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word) if "א" <= c <= "ת")


def _get(url: str, **params: Any) -> Any:
    response = requests.get(url, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=1024)
def _words(consonants: str) -> list[dict[str, Any]]:
    return _get(_API + consonants, never_split=1)


@lru_cache(maxsize=1024)
def _verse_words(ref: str) -> tuple[str, ...]:
    """The consonants of each word of a verse, such as "Ezekiel 40:2", in Sefaria's Masoretic text."""
    versions = _get(_TEXTS + ref, version="hebrew", return_format="text_only").get("versions") or [{}]
    return tuple(filter(None, map(_consonants, re.split(r"[\s־׀]+", versions[0].get("text", "")))))


def _surface_word(form: str, ref: str) -> Maybe[str]:
    """The word of the verse that this prefix-less form is written in, such as כמבנה for מִבְנֵה."""
    consonants = _consonants(form)
    return next((word for word in _verse_words(ref) if consonants and word.endswith(consonants)), None)


def lookup(word: str, strong_number: str, attestations: tuple[tuple[str, str], ...] = ()) -> Maybe[SefariaLexicon]:
    """The Sefaria entry for a word with this Strong's number, or None when Sefaria has none.

    Sefaria is asked for the bare consonants, since its pointing can differ from the OSHB's, and the Strong's
    number picks out the entry. Sefaria files many entries only under the words as written in the Bible,
    prefixes and all, so when the lemma finds nothing each attested ``(form, verse)`` is looked up as it
    stands in its verse. Raises ``requests.RequestException`` when Sefaria cannot be reached.
    """
    # Lazily, so verses are fetched only once the lemma has found nothing
    queries = itertools.chain([_consonants(word)], (_surface_word(form, ref) for form, ref in attestations))
    for query in queries:
        if query and (entry := find_entry(_words(query), strong_number)) is not None:
            return entry
    return None
