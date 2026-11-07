"""Verb roots and the weak classes that decide how they inflect."""

from dataclasses import dataclass
from enum import StrEnum

from hebrewenglish.common.maybe import Maybe

from .letters import (
    DAGESH,
    GUTTURALS,
    HIRIQ,
    HOLAM,
    SHIN_DOT,
    TSERE,
    base,
    clusters,
    has_vowel,
    letter,
)


class Weakness(StrEnum):
    I_GUTTURAL = "I-guttural"
    I_ALEPH = "I-aleph"
    I_NUN = "I-nun"
    I_YOD = "I-yod"
    II_GUTTURAL = "II-guttural"
    HOLLOW = "Hollow"
    GEMINATE = "Geminate"
    III_GUTTURAL = "III-guttural"
    III_ALEPH = "III-aleph"
    III_HE = "III-he"


class Hollow(StrEnum):
    """The long vowel a hollow verb shows where the strong verb has its second radical: qûm, śîm, bôʾ."""

    U = "û"
    I = "î"
    O = "ô"


@dataclass(frozen=True)
class Irregular:
    """A verb that borrows another class's behaviour in some stems."""

    # Stems (OSHB letters) in which the first radical behaves like a nun or a waw
    first_like_nun: frozenset[str] = frozenset()
    first_like_waw: frozenset[str] = frozenset()
    # nātan: the final nun assimilates to a following consonant, as in nātattā
    final_nun_assimilates: bool = False
    # A I-aleph verb whose aleph goes quiet in the Qal imperfect: yōʾmar
    aleph_quiescent: bool = False
    # A first he or ḥet that closes the syllable after a prefix, which the fit can also find: yihyeh
    guttural_closes: bool = False


IRREGULAR: dict[str, Irregular] = {
    "לקח": Irregular(first_like_nun=frozenset("q")),
    "הלכ": Irregular(first_like_waw=frozenset("qh")),
    "נתנ": Irregular(final_nun_assimilates=True),
    "היה": Irregular(guttural_closes=True),
    "חיה": Irregular(guttural_closes=True),
    # GKC §68
    **{
        bare: Irregular(aleph_quiescent=True)
        for bare in ("אמר", "אכל", "אבד", "אבה", "אפה", "אחז")
    },
}


@dataclass(frozen=True)
class VerbRoot:
    # Each radical in its medial form, keeping the shin or sin dot
    letters: tuple[str, str, str]
    weaknesses: frozenset[Weakness]
    hollow: Maybe[Hollow] = None
    # The Qal perfect's stem vowel, read from the lemma: šāmar a, kābēd ē, qāṭōn o
    perfect_theme: str = "a"

    @property
    def bare(self) -> str:
        return "".join(base(radical) for radical in self.letters)

    @property
    def irregular(self) -> Irregular:
        return IRREGULAR.get(self.bare, Irregular())

    @property
    def label(self) -> str:
        shown = [w for w in Weakness if w in self.weaknesses]
        # I-aleph is the guttural class's own subtype, so naming both says nothing more
        if Weakness.I_ALEPH in self.weaknesses:
            shown.remove(Weakness.I_GUTTURAL)
        return ", ".join(shown) if shown else "Strong"


_MATRES = {"וּ": Hollow.U, "וֹ": Hollow.O}


def _radicals(lemma: str) -> tuple[list[str], Maybe[Hollow], str]:
    """The lemma's consonants, the hollow vowel if a mater stands for the second radical, and the perfect vowel."""
    consonants: list[str] = []
    points: list[str] = []
    hollow: Maybe[Hollow] = None
    for cluster in clusters(lemma):
        bare = base(cluster)
        if not "א" <= bare <= "ת":
            continue
        marks = "".join(sorted(c for c in cluster[1:] if c not in "ׁׂ"))
        previous = points[-1] if points else ""
        bare_previous = consonants and not has_vowel(previous) and "ְ" not in previous
        if bare == "ו" and bare_previous and marks in (DAGESH, HOLAM):
            hollow = Hollow.U if marks == DAGESH else Hollow.O
            continue
        if bare == "י" and not marks and (HIRIQ in previous or TSERE in previous):
            hollow = Hollow.I
            continue
        consonants.append(letter(cluster))
        points.append(marks)
    theme = "a"
    if len(points) >= 2:
        theme = "ē" if TSERE in points[1] else "o" if HOLAM in points[1] else "a"
    return consonants, hollow, theme


def _consonants(text: str) -> list[str]:
    return [
        letter(cluster) for cluster in clusters(text) if "א" <= base(cluster) <= "ת"
    ]


def _weaknesses(
    first: str, middle: str, last: str, hollow: Maybe[Hollow], mappiq: bool
) -> frozenset[Weakness]:
    weaknesses: set[Weakness] = set()
    if first in GUTTURALS:
        weaknesses.add(Weakness.I_GUTTURAL)
    if first == "א":
        weaknesses.add(Weakness.I_ALEPH)
    if first == "נ":
        weaknesses.add(Weakness.I_NUN)
    if first in "יו":
        weaknesses.add(Weakness.I_YOD)
    if hollow is not None:
        weaknesses.add(Weakness.HOLLOW)
    elif middle in GUTTURALS:
        weaknesses.add(Weakness.II_GUTTURAL)
    if hollow is None and middle == last:
        weaknesses.add(Weakness.GEMINATE)
    # A final he with mappiq (gābah) is a consonant; without it, the he only marks the final vowel (bānâ)
    if last == "ה" and not mappiq:
        weaknesses.add(Weakness.III_HE)
    elif last in "חעה":
        weaknesses.add(Weakness.III_GUTTURAL)
    elif last == "א":
        weaknesses.add(Weakness.III_ALEPH)
    return frozenset(weaknesses)


def verb_root(root: Maybe[str], lemma: str) -> Maybe[VerbRoot]:
    """The root of a verb from its lexical-index root and its lemma, or None when it is not triliteral."""
    consonants, hollow, theme = _radicals(lemma)
    if hollow is not None and len(consonants) == 2:
        consonants.insert(1, "י" if hollow is Hollow.I else "ו")
    else:
        # A mater beside three consonants is just a long vowel, not a missing radical
        hollow = None
        # The index root decides which letters are radicals; the lemma only adds the shin and sin dots
        from_root = _consonants(root or "")
        if len(from_root) == 3 and [base(c) for c in from_root] != [
            base(c) for c in consonants
        ]:
            consonants = from_root
        if len(consonants) != 3:
            return None
    # An undotted shin is read as shin
    first, second, third = (c + SHIN_DOT if c == "ש" else c for c in consonants)
    mappiq = bool(lemma) and DAGESH in clusters(lemma)[-1]
    weaknesses = _weaknesses(base(first), base(second), base(third), hollow, mappiq)
    if Weakness.I_YOD in weaknesses:
        # Originally I-waw verbs are written with yod in the lexicon, and inflect alike
        first = "י"
    return VerbRoot((first, second, third), weaknesses, hollow, theme)
