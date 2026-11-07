"""Turn a paradigm template into a pointed Tiberian form by applying the sound rules of the weak radicals.

A template is a space-separated list of units ``C[:]V``:

- ``C`` is a radical ``1``/``2``/``3``, ``T`` for the Hithpael's ת, or a literal letter;
- ``:`` doubles the letter (dagesh forte);
- ``V`` is the vowel: ``a ā e ē i o u å`` (qamats hatuf), ``ə`` vocal shewa, ``ă ĕ ŏ`` hatefs, ``0`` silent
  shewa, ``0-`` a silent shewa that was once vocal and so leaves a following begadkefat letter soft (kitbî),
  ``î ô û ê è`` a vowel with its mater, ``ə!`` a final shewa that is written, or nothing.

Two codes stand for vowels the rules settle later: ``I`` is the Qal imperfect's prefix hiriq, which a following
guttural recolours, and ``E`` is the segol of an apocopated form, which becomes patah beside a guttural.
"""

import unicodedata
from dataclasses import dataclass, field, replace

from hebrewenglish.common.maybe import Maybe

from .letters import (
    BEGADKEFAT,
    DAGESH,
    FINAL_FORMS,
    GUTTURALS,
    HATEF_PATAH,
    HATEF_QAMATS,
    HATEF_SEGOL,
    HIRIQ,
    HOLAM,
    NO_DOUBLING,
    PATAH,
    QAMATS,
    QIBBUTS,
    SEGOL,
    SHEWA,
    SIBILANTS,
    TSERE,
    base,
)
from .roots import VerbRoot, Weakness

_GLYPHS = {
    "a": PATAH,
    "ā": QAMATS,
    "å": QAMATS,
    "e": SEGOL,
    "ē": TSERE,
    "i": HIRIQ,
    "o": HOLAM,
    "u": QIBBUTS,
    "ə": SHEWA,
    "ə!": SHEWA,
    "0-": SHEWA,
    "ă": HATEF_PATAH,
    "ĕ": HATEF_SEGOL,
    "ŏ": HATEF_QAMATS,
}
# Vowels written with a following mater, and the mater's letter and point
_MATRES = {
    "î": (HIRIQ, "י"),
    "ê": (TSERE, "י"),
    "è": (SEGOL, "י"),
    "ô": ("", "ו" + HOLAM),
    "û": ("", "ו" + DAGESH),
}
_HATEF_OF = {"a": "ă", "e": "ĕ", "å": "ŏ", "ā": "ŏ", "o": "ŏ"}
_FULL_OF = {"ă": "a", "ĕ": "e", "ŏ": "å"}
# Compensatory lengthening before a letter that cannot be doubled
_LENGTHENED = {"i": "ē", "I": "ē", "a": "ā", "u": "o", "å": "ā"}


def silent(vowel: str) -> bool:
    return vowel in ("0", "0-")


@dataclass
class Unit:
    letter: str
    vowel: str
    doubled: bool = False
    # Which radical this is, or 0 for a prefix or ending
    radical: int = 0


@dataclass(frozen=True)
class Params:
    """Lexical choices the rules cannot predict; fitted per verb from its attested forms."""

    # Stem vowel of the Qal imperfect, imperative and infinitive construct: yišmōr o, yikbad a, yēšēb ē
    imperfect_theme: str = "o"
    # Whether a I-yod verb was originally I-waw (yēšēb, hôšîb) or is truly I-yod (yîṭab, hêṭîb)
    waw_original: bool = True
    # Whether a first he or ḥet closes its syllable after a prefix (yihyeh, yaḥšōb) instead of taking a hatef
    guttural_closes: bool = False

    @property
    def wayyiqtol_theme(self) -> str:
        # The accent draws back onto the prefix after waw-consecutive, shortening a tsere: wayyēšeb
        return "e" if self.imperfect_theme == "ē" else self.imperfect_theme


@dataclass(frozen=True)
class Context:
    root: VerbRoot
    stem: str
    # The OSHB verb-type letter, e.g. "v" for imperative
    typ: str = ""
    params: Params = field(default_factory=Params)


def parse(template: str) -> list[Unit]:
    units: list[Unit] = []
    for token in template.split():
        head, rest = token[0], token[1:]
        if rest[:1] in ("ׁ", "ׂ"):
            head, rest = head + rest[0], rest[1:]
        doubled = rest.startswith(":")
        vowel = rest[1:] if doubled else rest
        radical = int(head) if head in "123" else 0
        units.append(Unit(head, vowel, doubled, radical))
    return units


def _first_radical(units: list[Unit]) -> Maybe[int]:
    return next((i for i, unit in enumerate(units) if unit.radical == 1), None)


def _neighbours(units: list[Unit], i: int) -> tuple[Maybe[Unit], Maybe[Unit]]:
    previous = units[i - 1] if i > 0 else None
    following = units[i + 1] if i + 1 < len(units) else None
    return previous, following


def _i_yod(units: list[Unit], ctx: Context) -> None:
    """The first radical of an originally I-waw verb survives only as a long prefix vowel: yēšēb, nôšab, hôšîb."""
    index = _first_radical(units)
    if index is None or index == 0:
        return
    unit, prefix = units[index], units[index - 1]
    if unit.doubled:
        unit.letter = "ו"
        return
    if not silent(unit.vowel):
        return
    waw = ctx.params.waw_original or ctx.stem in ctx.root.irregular.first_like_waw
    vowel = {
        "q": "ē" if waw else "î",
        "N": "ô",
        "h": "ô" if waw else "ê",
        "H": "û",
    }.get(ctx.stem)
    if vowel is not None:
        prefix.vowel = vowel
        del units[index]


def _i_aleph(units: list[Unit]) -> None:
    """yōʾmar: the aleph loses its consonantal value after an o prefix vowel; the 1cs writes only one aleph."""
    index = _first_radical(units)
    if index is None or index == 0 or not silent(units[index].vowel):
        return
    prefix = units[index - 1]
    prefix.vowel = "o"
    if base(prefix.letter) == "א":
        del units[index]
    else:
        units[index].vowel = ""


def _assimilate_first_nun(units: list[Unit], ctx: Context) -> None:
    """A first nun closing the prefix's syllable doubles the next radical instead: yippōl, niṣṣal, hiṣṣîl."""
    index = _first_radical(units)
    if (
        index is None
        or index == 0
        or index + 1 == len(units)
        or not silent(units[index].vowel)
    ):
        return
    nun, following = units[index], units[index + 1]
    like_nun = ctx.stem in ctx.root.irregular.first_like_nun
    if (base(nun.letter) == "נ" or like_nun) and base(
        following.letter
    ) not in NO_DOUBLING:
        following.doubled = True
        if units[index - 1].vowel == "å":
            # The Hophal prefix takes qibbuts before the doubling: huggad
            units[index - 1].vowel = "u"
        del units[index]


def _assimilate_final_nun(units: list[Unit]) -> None:
    """nātattā: nātan's final nun assimilates to the taw or nun of an ending."""
    for i, unit in enumerate(units[:-1]):
        if (
            unit.radical == 3
            and silent(unit.vowel)
            and base(units[i + 1].letter) in "תנ"
        ):
            units[i + 1].doubled = True
            del units[i]
            return


def _hithpael(units: list[Unit]) -> None:
    index = next((i for i, unit in enumerate(units) if unit.letter == "T"), None)
    if index is None:
        return
    taw = units[index]
    taw.letter = "ת"
    if index + 1 == len(units):
        return
    first = units[index + 1]
    if base(first.letter) in SIBILANTS:
        # hištammēr: the taw and a sibilant first radical change places, and the taw takes the sibilant's voice
        replacement = {"צ": "ט", "ז": "ד"}.get(base(first.letter), "ת")
        taw.letter, taw.radical, first.letter, first.radical = (
            first.letter,
            first.radical,
            replacement,
            0,
        )
    elif base(first.letter) in "דטת":
        first.doubled = True
        del units[index]


def _apocope(units: list[Unit]) -> None:
    """Settle the vowels of a shortened form (yiben, wayyaʿaś, yēṭ), whose template marks its segol E."""
    for i, unit in enumerate(units):
        if (
            i > 0
            and unit.vowel == "E"
            and unit.radical == 1
            and base(unit.letter) == "נ"
        ):
            # *yinṭ: the nun assimilates, and the doubling falls away at the end of the word: yēṭ, Hiphil yaṭ
            prefix = units[i - 1]
            prefix.vowel = {"I": "ē", "E": "a"}.get(prefix.vowel, prefix.vowel)
            del units[i]
            break
    for i, unit in enumerate(units):
        _, following = _neighbours(units, i)
        before_guttural = (
            following is not None
            and following.vowel == "E"
            and base(following.letter) in GUTTURALS
        )
        if unit.vowel == "E":
            unit.vowel = (
                "a" if base(unit.letter) in GUTTURALS or before_guttural else "e"
            )
        elif unit.vowel == "I" and before_guttural:
            unit.vowel = "a"


def _doubling(units: list[Unit]) -> None:
    for i, unit in enumerate(units):
        if not unit.doubled or base(unit.letter) not in NO_DOUBLING:
            continue
        unit.doubled = False
        # Aleph, ayin and resh lengthen the vowel before them; he and ḥet are doubled virtually, except as the
        # first radical, where the Niphal prefix still lengthens: yēʿāzēb, yēḥāšēb
        if i > 0 and (base(unit.letter) in "אער" or unit.radical == 1):
            units[i - 1].vowel = _LENGTHENED.get(units[i - 1].vowel, units[i - 1].vowel)


def _qal_prefix_vowel(letter: str, ctx: Context, closes: bool) -> str:
    """The Qal imperfect's prefix vowel before a first guttural."""
    a_theme = ctx.params.imperfect_theme != "o"
    if closes:
        if ctx.root.bare in ("היה", "חיה"):
            return "i"
        # yehgeh, yehdōp, yeḥdal, but yaḥteh, yaḥbōš
        return "e" if letter == "ה" or a_theme else "a"
    if Weakness.III_HE in ctx.root.weaknesses:
        # yaʿăśeh, but yeḥĕzeh
        return "a" if letter == "ע" else "e"
    # yeʾĕsōp, yeḥĕzaq, but yaʿămōd
    return "e" if letter == "א" or a_theme else "a"


def _guttural_after_prefix(prefix: Unit, unit: Unit, ctx: Context) -> None:
    """A guttural that would close the prefix's syllable takes a hatef in the prefix's colour, or closes it."""
    closes = (
        unit.radical == 1 and base(unit.letter) in "הח" and ctx.params.guttural_closes
    )
    if prefix.vowel == "I":
        prefix.vowel = _qal_prefix_vowel(base(unit.letter), ctx, closes)
    elif prefix.vowel == "i":
        # The Niphal and Hiphil prefixes, neʿĕzab and heʿĕmîd, or the imperative's i before a second radical, zaʿăqî
        prefix.vowel = "e" if unit.radical == 1 else "a"
    if not closes:
        unit.vowel = _HATEF_OF.get(prefix.vowel, "ă")


def _gutturals(units: list[Unit], ctx: Context) -> None:
    """Gutturals take no vocal shewa, and resist closing a syllable after a prefix."""
    for i, unit in enumerate(units):
        letter = base(unit.letter)
        # A third-radical guttural ends the stem, and _third_guttural and _third_aleph handle it
        if letter not in GUTTURALS or (unit.radical == 3 and unit.vowel != "ə"):
            continue
        previous, following = _neighbours(units, i)
        if unit.vowel == "ə":
            # ʾĕmōr, but ʾăkaltem: only the imperative and infinitive take hatef segol under a first aleph
            unit.vowel = (
                "ĕ" if letter == "א" and i == 0 and ctx.typ in ("v", "c") else "ă"
            )
        elif (
            silent(unit.vowel)
            and previous is not None
            and following is not None
            and unit.radical in (1, 2)
        ):
            _guttural_after_prefix(previous, unit, ctx)
    # A hatef before a vocal shewa opens into its full vowel, and the shewa falls silent: yaʿamdû, neʿezbû
    for i, unit in enumerate(units[:-2]):
        following = units[i + 1]
        if unit.vowel in _FULL_OF and following.vowel == "ə":
            unit.vowel = _FULL_OF[unit.vowel]
            following.vowel = "0-"


def _third_guttural(units: list[Unit], ctx: Context) -> None:
    """A final ḥet or ayin wants an a-vowel before it: šāmaʿ, šillaḥ, šōmēaʿ, šāmaʿat."""
    for i, unit in enumerate(units):
        if unit.radical != 3 or base(unit.letter) not in "חע":
            continue
        previous, following = _neighbours(units, i)
        if following is None and unit.vowel == "" and previous is not None:
            if previous.vowel == "ē" and ctx.typ not in ("r", "s"):
                # šillaḥ, but the participle keeps its ē: məšallēaḥ
                previous.vowel = "a"
            if previous.vowel not in ("a", "ā", "ă"):
                # Furtive patah: an a-glide before the final guttural, written under it
                unit.vowel = "a"
        elif silent(unit.vowel) and following is not None and following.vowel == "ə!":
            # The 2fs perfect: šāmaʿat
            unit.vowel = "a"
        elif (
            previous is not None
            and unit.vowel == previous.vowel == "e"
            and i == len(units) - 2
            and units[-1].letter == "ת"
        ):
            # A segolate ending beside a guttural takes patah: šōmaʿat
            unit.vowel = previous.vowel = "a"


def _third_aleph(units: list[Unit], ctx: Context) -> None:
    """A final aleph goes quiet and lengthens the vowel before it: māṣāʾ, māṣāʾtā."""
    for i, unit in enumerate(units):
        if (
            unit.radical != 3
            or base(unit.letter) != "א"
            or not (silent(unit.vowel) or unit.vowel == "")
        ):
            continue
        unit.vowel = ""
        previous, following = _neighbours(units, i)
        if following is not None and following.vowel == "ə!":
            following.vowel = ""
        if previous is None:
            continue
        if following is not None and following.letter == "נ":
            if previous.vowel in ("a", "ē"):
                previous.vowel = "e"
        elif previous.vowel == "a":
            previous.vowel = "ā" if following is None or ctx.stem == "q" else "ē"


def apply_rules(units: list[Unit], ctx: Context) -> list[Unit]:
    root, irregular = ctx.root, ctx.root.irregular
    units = [replace(unit) for unit in units]
    for unit in units:
        if unit.radical:
            unit.letter = root.letters[unit.radical - 1]
    if Weakness.I_YOD in root.weaknesses or ctx.stem in irregular.first_like_waw:
        _i_yod(units, ctx)
    if irregular.aleph_quiescent and ctx.stem == "q":
        _i_aleph(units)
    _assimilate_first_nun(units, ctx)
    if irregular.final_nun_assimilates:
        _assimilate_final_nun(units)
    _hithpael(units)
    _apocope(units)
    _doubling(units)
    _gutturals(units, ctx)
    _third_guttural(units, ctx)
    _third_aleph(units, ctx)
    for unit in units:
        if unit.vowel == "I":
            unit.vowel = "i"
    return units


def after_waw_consecutive(units: list[Unit]) -> list[Unit]:
    """A wayyiqtol without its וַ, which the OSHB writes apart, keeping the doubling it puts in the prefix."""
    first = units[0]
    # The 1cs aleph cannot be doubled, and a yod or nun under shewa gives its doubling up: wayəšallaḥ
    if base(first.letter) == "א" or (first.vowel == "ə" and base(first.letter) in "ינ"):
        return units
    return [replace(first, doubled=True), *units[1:]]


def spell(units: list[Unit]) -> str:
    """Write the units out as pointed text, adding dagesh lene, final forms and matres."""
    parts: list[str] = []
    for i, unit in enumerate(units):
        last = i == len(units) - 1
        letter = unit.letter
        closed_before = i == 0 or units[i - 1].vowel == "0"
        dagesh = (unit.doubled and not (last and unit.vowel == "")) or (
            base(letter) in BEGADKEFAT and closed_before
        )
        # A vowel written with a mater puts another letter after this one, so it is not word-final
        if last and base(letter) in FINAL_FORMS and unit.vowel not in _MATRES:
            letter = FINAL_FORMS[base(letter)] + letter[1:]
        point, mater = _MATRES.get(unit.vowel, (_GLYPHS.get(unit.vowel, ""), ""))
        if silent(unit.vowel):
            point = SHEWA if not last or base(unit.letter) == "כ" else ""
        elif unit.vowel == "" and last and base(unit.letter) == "כ":
            point = SHEWA
        parts.append(letter + (DAGESH if dagesh else "") + point + mater)
    return unicodedata.normalize("NFC", "".join(parts))
