from dataclasses import dataclass
from functools import cached_property

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.common.strong import Strong, parse_strong
from hebrewenglish.lexicon import res
from hebrewenglish.lexicon.res import StrongLexiconEntry
from hebrewenglish.lexicon.similar import HebrewIndex, IndexedLemma


@dataclass(frozen=True)
class FormRecord:
    """One pointed spelling of a word, with the verses it occurs in (OSHB references such as "Gen.2.15")."""

    text: str
    count: int
    refs: list[str]


@dataclass(frozen=True)
class LemmaMorphology:
    """Every attested form of one OSHB lemma, keyed by its whole morphology code, such as "HNcfsc/Sp3ms"."""

    key: str
    lemma: Maybe[str]
    xlit: Maybe[str]
    gloss: Maybe[str]
    pos: Maybe[str]
    lang: str
    count: int
    index: Maybe[str]
    usages: dict[str, list[FormRecord]]


def lemma_morphology(key: str, record: dict) -> LemmaMorphology:
    return LemmaMorphology(
        key=key,
        lemma=record.get("lemma"),
        xlit=record.get("xlit"),
        gloss=record.get("gloss"),
        pos=record.get("pos"),
        lang=record.get("lang", "heb"),
        count=record.get("count", 0),
        index=record.get("index"),
        usages={
            code: [
                FormRecord(form["text"], form["count"], form["refs"])
                for form in usage["forms"]
            ]
            for code, usage in record["usages"].items()
        },
    )


class Backend:
    prefer_aramaic: bool = False
    permit_proper_nouns: bool = False

    def __init__(self):
        # The matcher reports positions in the Strong's lexicon, not ids
        self._strong_ids = list(res.STRONG_LEXICON.entries)
        # Split entries such as H122 have one lemma per letter ("122a", "122b")
        self._morph_keys: dict[str, list[str]] = {}
        for key, record in res.MORPH_DATA.items():
            if "strong" in record:
                self._morph_keys.setdefault(record["strong"], []).append(key)

    def search_string(self, input: str, n: int = 8) -> list[Strong]:
        """Given a word, find a list of Strong's numbers that match the word, in decreasing order of preference.

        Args:
            input (str): The input to match against
            n (int): How many numbers to return

        Returns:
            list[Strong]: The id's in decreasing order of preference
        """
        if not input.strip():
            return []
        found = (
            parse_strong(self._strong_ids[i][1:])
            for i, _ in res.STRONG_MATCHER.get_matches(input.strip(), n)
        )
        return [strong for strong in found if strong is not None]

    @cached_property
    def _hebrew_index(self) -> HebrewIndex:
        # Built on the first Hebrew search, since it reads every attested form
        return HebrewIndex(
            IndexedLemma(
                key,
                record["lemma"],
                tuple(form["text"] for usage in record["usages"].values() for form in usage["forms"]),
                _index_root(record.get("index")),
                record.get("count", 0),
            )
            for key, record in res.MORPH_DATA.items()
            if record.get("lemma") and parse_strong(key) is not None
        )

    def search_hebrew(self, input: str, n: int = 8) -> list[Strong]:
        """Given a Hebrew word, pointed or not, find the lemmas spelled most like it, best first.

        Args:
            input (str): The Hebrew word, as written in a dictionary or inflected in a verse
            n (int): How many lemmas to return

        Returns:
            list[Strong]: One per lemma, a split entry's lemma carrying its letter ("122a")
        """
        found = (parse_strong(key) for key in self._hebrew_index.search(input, n))
        return [strong for strong in found if strong is not None]

    def get_lexicon_entry(self, strong_number: Strong) -> Maybe[StrongLexiconEntry]:
        """Given a Strong's number, return the corresponding lexicon entry.

        Args:
            strong_number (Strong): The Strong's number to look up

        Returns:
            Maybe[StrongLexiconEntry]: The lexicon entry corresponding to the Strong's number
        """
        return res.STRONG_LEXICON.entries.get(f"H{strong_number.index}")

    def get_morphology(self, strong_number: Strong) -> list[LemmaMorphology]:
        """Given a Strong's number, return the attested forms of each lemma filed under it.

        Args:
            strong_number (Strong): The Strong's number to look up; a modifier picks out one lemma of a split entry
        Returns:
            list[LemmaMorphology]: One per lemma, usually just one, and none when the number has no morphology
        """
        keys = self._morph_keys.get(f"H{strong_number.index}", [])
        if strong_number.modifier is not None:
            keys = [
                key
                for key in keys
                if key == f"{strong_number.index}{strong_number.modifier}"
            ]
        return [lemma_morphology(key, res.MORPH_DATA[key]) for key in keys]

    def root(self, lemma: LemmaMorphology) -> Maybe[str]:
        """The consonantal root of a lemma, read from the lexical index.

        Only the main entry of a word group records its root, so derived words borrow it from a related entry.
        """
        return _index_root(lemma.index)


def _index_root(index_id: Maybe[str]) -> Maybe[str]:
    entry = res.INDEX.get(index_id or "")
    if entry is None:
        return None
    if "root" in entry:
        return entry["root"]
    return next(
        (res.INDEX[r]["root"] for r in entry.get("related", []) if "root" in res.INDEX.get(r, {})),
        None,
    )
