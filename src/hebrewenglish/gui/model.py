"""View model for the Davar reverse-lexicon page.

These types mirror the Figma Make prototype's ``lexiconData.ts``. They hold display data only:
``gui/adapter.py`` fills them from the real lexicon and morphology, ``gui/demo.py`` by hand.
"""

import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from hebrewenglish.common.maybe import Maybe


class Attestation(StrEnum):
    ATTESTED = "attested"
    UNATTESTED = "unattested"


class Category(StrEnum):
    HEBREW = "hebrew"
    ARAMAIC = "aramaic"
    PROPER_NAME = "proper-name"
    PREPOSITION = "preposition"


class SuffixId(StrEnum):
    NONE = "none"
    P1CS = "1cs"
    P2MS = "2ms"
    P2FS = "2fs"
    P3MS = "3ms"
    P3FS = "3fs"
    P1CP = "1cp"
    P2MP = "2mp"
    P2FP = "2fp"
    P3MP = "3mp"
    P3FP = "3fp"


@dataclass(frozen=True)
class SuffixOption:
    id: SuffixId
    label: str
    verb: str
    noun: str
    transliteration: str


SUFFIX_OPTIONS: dict[SuffixId, SuffixOption] = {
    option.id: option
    for option in [
        SuffixOption(SuffixId.NONE, "None", "", "", ""),
        SuffixOption(SuffixId.P1CS, "1st person common singular", "נִי", "י", "nî"),
        SuffixOption(SuffixId.P2MS, "2nd person masculine singular", "ךָ", "ךָ", "kā"),
        SuffixOption(SuffixId.P2FS, "2nd person feminine singular", "ךְ", "ךְ", "k"),
        SuffixOption(SuffixId.P3MS, "3rd person masculine singular", "הוּ", "וֹ", "hû"),
        SuffixOption(SuffixId.P3FS, "3rd person feminine singular", "הָ", "הּ", "hā"),
        SuffixOption(SuffixId.P1CP, "1st person common plural", "נוּ", "נוּ", "nû"),
        SuffixOption(SuffixId.P2MP, "2nd person masculine plural", "כֶם", "כֶם", "kem"),
        SuffixOption(SuffixId.P2FP, "2nd person feminine plural", "כֶן", "כֶן", "ken"),
        SuffixOption(SuffixId.P3MP, "3rd person masculine plural", "ם", "ם", "m"),
        SuffixOption(SuffixId.P3FP, "3rd person feminine plural", "ן", "ן", "n"),
    ]
}


@dataclass(frozen=True)
class MorphologyRow:
    label: str
    form: str
    transliteration: str
    attestation: Attestation
    note: Maybe[str] = None
    alternative: Maybe[str] = None
    references: tuple[str, ...] = ()
    # Identifies the row in suffixed_forms when its form alone would not, e.g. a slot only attested with a suffix
    key: Maybe[str] = None

    @property
    def suffix_key(self) -> str:
        return self.key or self.form


@dataclass
class MorphologyGroup:
    id: str
    label: str
    description: str
    rows: list[MorphologyRow]
    # The verbal stem (Qal, Niphal…) a group belongs to; groups of other parts of speech have none
    stem: Maybe[str] = None


@dataclass(frozen=True)
class Property:
    label: str
    value: str
    hebrew: bool = False


@dataclass(frozen=True)
class ResolvedForm:
    """A morphology row after applying a pronominal suffix, split so the suffix can be highlighted."""

    base: str
    suffix: str
    form: str
    transliteration: str
    attestation: Attestation
    references: tuple[str, ...] = ()


@dataclass
class LexicalResult:
    id: str
    part_of_speech: str
    category: Category
    lemma: str
    transliteration: str
    short_definition: str
    long_definition: str
    properties: list[Property]
    morphology: list[MorphologyGroup]
    category_label: Maybe[str] = None
    # Attested suffixed forms, keyed by (row suffix key, suffix)
    suffixed_forms: dict[tuple[str, SuffixId], ResolvedForm] = field(
        default_factory=dict
    )
    # Whether a suffix missing from suffixed_forms is built by joining base and suffix, or left out
    reconstruct_suffixes: bool = True
    # The Strong's number ("8104") that picks out the entry in other lexicons, when the result has one
    strong_number: Maybe[str] = None
    # How often the lemma occurs in the Hebrew Bible, when the morphology knows
    occurrences: Maybe[int] = None

    @property
    def root(self) -> str:
        return next(
            (p.value for p in self.properties if p.label in ("Root", "Base")), ""
        )

    @property
    def visible_groups(self) -> list[MorphologyGroup]:
        # Nouns take possessive suffixes through the suffix control instead of a fixed tab
        if self.part_of_speech == "Noun":
            return [group for group in self.morphology if group.id != "suffixes"]
        return self.morphology

    @property
    def stems(self) -> list[str]:
        return list(
            dict.fromkeys(
                group.stem for group in self.morphology if group.stem is not None
            )
        )

    def groups_for(self, stem: Maybe[str]) -> list[MorphologyGroup]:
        """The visible groups of one stem, or all of them when the entry has no stems."""
        if not self.stems:
            return self.visible_groups
        return [group for group in self.visible_groups if group.stem == stem]

    @property
    def suffix_label(self) -> Maybe[str]:
        return {
            "Verb": "Object suffix",
            "Noun": "Possessive suffix",
            "Preposition": "Pronominal contraction",
        }.get(self.part_of_speech)


def resolve_form(
    row: MorphologyRow, result: LexicalResult, suffix_id: SuffixId
) -> Maybe[ResolvedForm]:
    """The row's form with the suffix applied, or None when there is no such form to show."""
    if suffix_id is SuffixId.NONE:
        if not row.form:
            return None
        return ResolvedForm(
            base=row.form,
            suffix="",
            form=row.form,
            transliteration=row.transliteration,
            attestation=row.attestation,
            references=row.references,
        )

    known = result.suffixed_forms.get((row.suffix_key, suffix_id))
    if known is not None:
        return known
    if not result.reconstruct_suffixes or not row.form:
        return None

    option = SUFFIX_OPTIONS[suffix_id]
    suffix = option.noun if result.part_of_speech == "Noun" else option.verb
    return ResolvedForm(
        base=row.form,
        suffix=suffix,
        form=row.form + suffix,
        transliteration=f"{row.transliteration}-{option.transliteration}",
        attestation=Attestation.UNATTESTED,
    )


def split_clusters(value: str) -> list[str]:
    """Split pointed Hebrew into letters, each carrying its vowel points and accents."""
    clusters: list[str] = []
    for character in value:
        if unicodedata.category(character).startswith("M") and clusters:
            clusters[-1] += character
        else:
            clusters.append(character)
    return clusters


def bare_consonant(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if not unicodedata.category(c).startswith("M")
    )


type Segment = tuple[Literal["root", "inflection", "suffix"], str]


def highlight_segments(resolved: ResolvedForm, root: str) -> list[Segment]:
    """Mark each letter of a form as part of the root, an inflection, or the pronominal suffix."""
    root_letters = [bare_consonant(cluster) for cluster in split_clusters(root)]
    root_index = 0
    segments: list[Segment] = []
    for cluster in split_clusters(resolved.base):
        # Without a known root nothing can be told apart as inflection
        if not root_letters:
            segments.append(("root", cluster))
        elif (
            root_index < len(root_letters)
            and bare_consonant(cluster) == root_letters[root_index]
        ):
            root_index += 1
            segments.append(("root", cluster))
        else:
            segments.append(("inflection", cluster))
    if resolved.suffix:
        segments.append(("suffix", resolved.suffix))
    return segments


type ParadigmSlot = Literal["ms", "fs", "mp", "fp"]

PARADIGM_COLUMNS: list[tuple[ParadigmSlot, str]] = [
    ("ms", "Masculine"),
    ("fs", "Feminine"),
    ("mp", "Masculine"),
    ("fp", "Feminine"),
]


def paradigm_people(group: MorphologyGroup) -> list[str]:
    if "imperative" in group.id:
        return ["2nd"]
    if "participle" in group.id:
        return ["Participle"]
    return ["3rd", "2nd", "1st"]


def row_person(row: MorphologyRow, group: MorphologyGroup) -> str:
    for person in ("3rd", "2nd", "1st"):
        if row.label.startswith(person):
            return person
    return "2nd" if "imperative" in group.id else "Participle"


def row_matches_slot(row: MorphologyRow, slot: ParadigmSlot) -> bool:
    # Case-insensitive, unlike the prototype, so "Masculine singular" rows fill the imperative and participle tables
    label = row.label.lower()
    number = "singular" if slot.endswith("s") else "plural"
    gender = "masc" if slot.startswith("m") else "fem"
    return number in label and ("common" in label or gender in label)


def paradigm_row(
    group: MorphologyGroup, person: str, slot: ParadigmSlot
) -> Maybe[MorphologyRow]:
    return next(
        (
            row
            for row in group.rows
            if row_person(row, group) == person and row_matches_slot(row, slot)
        ),
        None,
    )
