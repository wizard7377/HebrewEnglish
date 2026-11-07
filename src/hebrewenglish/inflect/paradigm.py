"""Paradigm templates for each stem and conjugation, after Gesenius–Kautzsch–Cowley's verb tables.

Stems and conjugations are keyed by their OSHB letters (``q`` Qal, ``N`` Niphal…; ``p`` perfect, ``i``
imperfect…), cells by person, gender and number (``3ms``, ``2fp``; ``ms`` for participles, ``""`` for
infinitives). Placeholders in braces stand for the vowels that vary from verb to verb; ``_vowels`` lists them.
"""

from hebrewenglish.common.maybe import Maybe

from .render import (
    Context,
    Params,
    Unit,
    after_waw_consecutive,
    apply_rules,
    parse,
    spell,
)
from .roots import VerbRoot, Weakness

type Table = dict[str, Maybe[str]]
type StemTables = dict[str, Table]

PERFECT, SEQ_PERFECT, IMPERFECT, SEQ_IMPERFECT = "p", "q", "i", "w"
COHORTATIVE, JUSSIVE, IMPERATIVE = "h", "j", "v"
ACTIVE_PARTICIPLE, PASSIVE_PARTICIPLE, INF_ABSOLUTE, INF_CONSTRUCT = "r", "s", "a", "c"

PERFECT_CELLS = ["3ms", "3fs", "2ms", "2fs", "1cs", "3cp", "2mp", "2fp", "1cp"]
IMPERFECT_CELLS = ["3ms", "3fs", "2ms", "2fs", "1cs", "3mp", "3fp", "2mp", "2fp", "1cp"]
CELLS: dict[str, list[str]] = {
    PERFECT: PERFECT_CELLS,
    SEQ_PERFECT: PERFECT_CELLS,
    IMPERFECT: IMPERFECT_CELLS,
    SEQ_IMPERFECT: IMPERFECT_CELLS,
    JUSSIVE: [cell for cell in IMPERFECT_CELLS if cell[0] != "1"],
    COHORTATIVE: ["1cs", "1cp"],
    IMPERATIVE: ["2ms", "2fs", "2mp", "2fp"],
    ACTIVE_PARTICIPLE: ["ms", "fs", "mp", "fp"],
    PASSIVE_PARTICIPLE: ["ms", "fs", "mp", "fp"],
    INF_ABSOLUTE: [""],
    INF_CONSTRUCT: [""],
}

_ACTIVE = [
    PERFECT,
    SEQ_PERFECT,
    IMPERFECT,
    SEQ_IMPERFECT,
    COHORTATIVE,
    JUSSIVE,
    IMPERATIVE,
    ACTIVE_PARTICIPLE,
]
_PASSIVE = [PERFECT, SEQ_PERFECT, IMPERFECT, SEQ_IMPERFECT, PASSIVE_PARTICIPLE]
# The conjugations each stem has; Pual and Hophal have no imperative, cohortative or active participle
TYPES: dict[str, list[str]] = {
    "q": [*_ACTIVE, PASSIVE_PARTICIPLE, INF_ABSOLUTE, INF_CONSTRUCT],
    **{stem: [*_ACTIVE, INF_ABSOLUTE, INF_CONSTRUCT] for stem in "Npthomrz"},
    **{stem: [*_PASSIVE, INF_ABSOLUTE, INF_CONSTRUCT] for stem in "PHOM"},
}
# Polel, Poel and their passive and reflexive inflect like Piel, Pual and Hithpael with ō for the doubling
POLEL = {"o": "p", "m": "p", "O": "P", "M": "P", "r": "t", "z": "t"}


def perfect(ms: str, voc: str, cons: str, plural: Maybe[str] = None) -> Table:
    """The perfect from its 3ms, its stem before a vowel ending, and its stem before a consonant ending."""
    plural = plural or cons
    return {
        "3ms": ms,
        "3fs": voc + "ā ה",
        "2ms": cons + " תā",
        # The 2fs ending is a bare taw, written with shewa only after a closed syllable
        "2fs": cons + " ת" + ("ə!" if cons.endswith("0") else ""),
        "1cs": cons + " תî",
        "3cp": voc + "û",
        "2mp": plural + " תe ם",
        "2fp": plural + " תe ן",
        "1cp": cons + " נû",
    }


def imperfect(prefixes: str, body: str, voc: str, fp: Maybe[str]) -> Table:
    """The imperfect from its 3ms/1cs/3fs/1cp prefixes, its stem, its stem before a vowel ending, and its -nâ stem."""
    y, t, a, n = prefixes.split()
    return {
        "3ms": f"{y} {body}",
        "3fs": f"{t} {body}",
        "2ms": f"{t} {body}",
        "2fs": f"{t} {voc}î",
        "1cs": f"{a} {body}",
        "3mp": f"{y} {voc}û",
        "3fp": fp and f"{t} {fp}",
        "2mp": f"{t} {voc}û",
        "2fp": fp and f"{t} {fp}",
        "1cp": f"{n} {body}",
    }


def cohortative(prefixes: str, body: str) -> Table:
    _, _, a, n = prefixes.split()
    return {"1cs": f"{a} {body}", "1cp": f"{n} {body}"}


def imperative(ms: str, voc: str, fp: Maybe[str]) -> Table:
    return {"2ms": ms, "2fs": voc + "î", "2mp": voc + "û", "2fp": fp}


def participle(ms: str, fs: str, voc: str) -> Table:
    return {"ms": ms, "fs": fs, "mp": voc + "î ם", "fp": voc + "ô ת"}


def jussive(prefixes: str, body: str) -> Table:
    """The short 3ms/3fs/2ms jussive; the other persons are the imperfect's."""
    y, t, _, _ = prefixes.split()
    return {"3ms": f"{y} {body}", "3fs": f"{t} {body}", "2ms": f"{t} {body}"}


def inf(form: Maybe[str]) -> Table:
    return {"": form} if form else {}


STRONG: dict[str, StemTables] = {
    "q": {
        PERFECT: perfect("1ā 2{P} 3", "1ā 2ə 3", "1ā 2{Q} 30", "1ə 2{Q} 30"),
        IMPERFECT: imperfect("יI תI אe נI", "10 2{T} 3", "10 2ə 3", "10 2{T} 30 נā ה"),
        COHORTATIVE: cohortative("יI תI אe נI", "10 2ə 3ā ה"),
        IMPERATIVE: imperative("1ə 2{T} 3", "1i 20- 3", "1ə 2{T} 30 נā ה"),
        ACTIVE_PARTICIPLE: participle("1o 2ē 3", "1o 2e 3e ת", "1o 2ə 3"),
        PASSIVE_PARTICIPLE: participle("1ā 2û 3", "1ə 2û 3ā ה", "1ə 2û 3"),
        INF_ABSOLUTE: inf("1ā 2o 3"),
        INF_CONSTRUCT: inf("1ə 2{T} 3"),
    },
    "N": {
        PERFECT: perfect("נi 10 2a 3", "נi 10 2ə 3", "נi 10 2a 30"),
        IMPERFECT: imperfect("יi תi אi נi", "1:ā 2ē 3", "1:ā 2ə 3", "1:ā 2a 30 נā ה"),
        COHORTATIVE: cohortative("יi תi אi נi", "1:ā 2ə 3ā ה"),
        IMPERATIVE: imperative("הi 1:ā 2ē 3", "הi 1:ā 2ə 3", "הi 1:ā 2a 30 נā ה"),
        ACTIVE_PARTICIPLE: participle("נi 10 2ā 3", "נi 10 2e 3e ת", "נi 10 2ā 3"),
        INF_ABSOLUTE: inf("נi 10 2o 3"),
        INF_CONSTRUCT: inf("הi 1:ā 2ē 3"),
    },
    "p": {
        PERFECT: perfect("1i 2:ē 3", "1i 2:ə 3", "1i 2:a 30"),
        IMPERFECT: imperfect("יə תə אă נə", "1a 2:ē 3", "1a 2:ə 3", "1a 2:ē 30 נā ה"),
        COHORTATIVE: cohortative("יə תə אă נə", "1a 2:ə 3ā ה"),
        IMPERATIVE: imperative("1a 2:ē 3", "1a 2:ə 3", "1a 2:ē 30 נā ה"),
        ACTIVE_PARTICIPLE: participle("מə 1a 2:ē 3", "מə 1a 2:e 3e ת", "מə 1a 2:ə 3"),
        # GKC gives qaṭṭōl, but the Bible far more often has qaṭṭēl, like the construct
        INF_ABSOLUTE: inf("1a 2:ē 3"),
        INF_CONSTRUCT: inf("1a 2:ē 3"),
    },
    "P": {
        PERFECT: perfect("1u 2:a 3", "1u 2:ə 3", "1u 2:a 30"),
        IMPERFECT: imperfect("יə תə אă נə", "1u 2:a 3", "1u 2:ə 3", "1u 2:a 30 נā ה"),
        PASSIVE_PARTICIPLE: participle("מə 1u 2:ā 3", "מə 1u 2:e 3e ת", "מə 1u 2:ā 3"),
        INF_ABSOLUTE: inf("1u 2:o 3"),
        INF_CONSTRUCT: inf("1u 2:a 3"),
    },
    "t": {
        PERFECT: perfect("הi T0 1a 2:ē 3", "הi T0 1a 2:ə 3", "הi T0 1a 2:a 30"),
        IMPERFECT: imperfect(
            "יi תi אe נi", "T0 1a 2:ē 3", "T0 1a 2:ə 3", "T0 1a 2:ē 30 נā ה"
        ),
        COHORTATIVE: cohortative("יi תi אe נi", "T0 1a 2:ə 3ā ה"),
        IMPERATIVE: imperative(
            "הi T0 1a 2:ē 3", "הi T0 1a 2:ə 3", "הi T0 1a 2:ē 30 נā ה"
        ),
        ACTIVE_PARTICIPLE: participle(
            "מi T0 1a 2:ē 3", "מi T0 1a 2:e 3e ת", "מi T0 1a 2:ə 3"
        ),
        INF_ABSOLUTE: inf("הi T0 1a 2:ē 3"),
        INF_CONSTRUCT: inf("הi T0 1a 2:ē 3"),
    },
    "h": {
        PERFECT: perfect("הi 10 2î 3", "הi 10 2î 3", "הi 10 2a 30"),
        IMPERFECT: imperfect("יa תa אa נa", "10 2î 3", "10 2î 3", "10 2ē 30 נā ה"),
        JUSSIVE: jussive("יa תa אa נa", "10 2ē 3"),
        COHORTATIVE: cohortative("יa תa אa נa", "10 2î 3ā ה"),
        IMPERATIVE: imperative("הa 10 2ē 3", "הa 10 2î 3", "הa 10 2ē 30 נā ה"),
        ACTIVE_PARTICIPLE: participle("מa 10 2î 3", "מa 10 2e 3e ת", "מa 10 2î 3"),
        INF_ABSOLUTE: inf("הa 10 2ē 3"),
        INF_CONSTRUCT: inf("הa 10 2î 3"),
    },
    "H": {
        PERFECT: perfect("הå 10 2a 3", "הå 10 2ə 3", "הå 10 2a 30"),
        IMPERFECT: imperfect("יå תå אå נå", "10 2a 3", "10 2ə 3", "10 2a 30 נā ה"),
        PASSIVE_PARTICIPLE: participle("מå 10 2ā 3", "מå 10 2e 3e ת", "מå 10 2ā 3"),
        INF_ABSOLUTE: inf("הå 10 2ē 3"),
        INF_CONSTRUCT: inf("הå 10 2a 3"),
    },
}


def _iii_he_perfect(
    ms: str, cons: str, fs: str, cp: str, plural: Maybe[str] = None
) -> Table:
    return perfect(ms, "", cons, plural) | {"3fs": fs, "3cp": cp}


# III-he verbs end in a vowel: bānâ, bānətâ, bānîtî, yibneh, and short jussives such as yiben
III_HE: dict[str, StemTables] = {
    "q": {
        PERFECT: _iii_he_perfect("1ā 2ā ה", "1ā 2î", "1ā 2ə תā ה", "1ā 2û", "1ə 2î"),
        IMPERFECT: imperfect("יI תI אe נI", "10 2e ה", "10 2", "10 2è נā ה"),
        JUSSIVE: jussive("יI תI אe נI", "1E 2"),
        COHORTATIVE: cohortative("יI תI אe נI", "10 2e ה"),
        IMPERATIVE: imperative("1ə 2ē ה", "1ə 2", "1ə 2è נā ה"),
        ACTIVE_PARTICIPLE: participle("1o 2e ה", "1o 2ā ה", "1o 2"),
        PASSIVE_PARTICIPLE: participle("1ā 2û י", "1ə 2û יā ה", "1ə 2û י"),
        INF_ABSOLUTE: inf("1ā 2o ה"),
        INF_CONSTRUCT: inf("1ə 2ô ת"),
    },
    "N": {
        PERFECT: _iii_he_perfect("נi 10 2ā ה", "נi 10 2ê", "נi 10 2ə תā ה", "נi 10 2û"),
        IMPERFECT: imperfect("יi תi אi נi", "1:ā 2e ה", "1:ā 2", "1:ā 2è נā ה"),
        JUSSIVE: jussive("יi תi אi נi", "1:ā 2"),
        COHORTATIVE: cohortative("יi תi אi נi", "1:ā 2e ה"),
        IMPERATIVE: imperative("הi 1:ā 2ē ה", "הi 1:ā 2", "הi 1:ā 2è נā ה"),
        ACTIVE_PARTICIPLE: participle("נi 10 2e ה", "נi 10 2ā ה", "נi 10 2"),
        INF_ABSOLUTE: inf("נi 10 2o ה"),
        INF_CONSTRUCT: inf("הi 1:ā 2ô ת"),
    },
    "p": {
        PERFECT: _iii_he_perfect("1i 2:ā ה", "1i 2:î", "1i 2:ə תā ה", "1i 2:û"),
        IMPERFECT: imperfect("יə תə אă נə", "1a 2:e ה", "1a 2:", "1a 2:è נā ה"),
        JUSSIVE: jussive("יə תə אă נə", "1a 2"),
        COHORTATIVE: cohortative("יə תə אă נə", "1a 2:e ה"),
        IMPERATIVE: imperative("1a 2:ē ה", "1a 2:", "1a 2:è נā ה"),
        ACTIVE_PARTICIPLE: participle("מə 1a 2:e ה", "מə 1a 2:ā ה", "מə 1a 2:"),
        INF_ABSOLUTE: inf("1a 2:o ה"),
        INF_CONSTRUCT: inf("1a 2:ô ת"),
    },
    "P": {
        PERFECT: _iii_he_perfect("1u 2:ā ה", "1u 2:ê", "1u 2:ə תā ה", "1u 2:û"),
        IMPERFECT: imperfect("יə תə אă נə", "1u 2:e ה", "1u 2:", "1u 2:è נā ה"),
        PASSIVE_PARTICIPLE: participle("מə 1u 2:e ה", "מə 1u 2:ā ה", "מə 1u 2:"),
        INF_CONSTRUCT: inf("1u 2:ô ת"),
    },
    "t": {
        PERFECT: _iii_he_perfect(
            "הi T0 1a 2:ā ה", "הi T0 1a 2:î", "הi T0 1a 2:ə תā ה", "הi T0 1a 2:û"
        ),
        IMPERFECT: imperfect(
            "יi תi אe נi", "T0 1a 2:e ה", "T0 1a 2:", "T0 1a 2:è נā ה"
        ),
        JUSSIVE: jussive("יi תi אe נi", "T0 1a 2"),
        COHORTATIVE: cohortative("יi תi אe נi", "T0 1a 2:e ה"),
        IMPERATIVE: imperative("הi T0 1a 2:ē ה", "הi T0 1a 2:", None),
        ACTIVE_PARTICIPLE: participle(
            "מi T0 1a 2:e ה", "מi T0 1a 2:ā ה", "מi T0 1a 2:"
        ),
        INF_CONSTRUCT: inf("הi T0 1a 2:ô ת"),
    },
    "h": {
        PERFECT: _iii_he_perfect("הi 10 2ā ה", "הi 10 2ê", "הi 10 2ə תā ה", "הi 10 2û"),
        IMPERFECT: imperfect("יa תa אa נa", "10 2e ה", "10 2", "10 2è נā ה"),
        JUSSIVE: jussive("יE תE אE נE", "1E 2"),
        COHORTATIVE: cohortative("יa תa אa נa", "10 2e ה"),
        IMPERATIVE: imperative("הa 10 2ē ה", "הa 10 2", None),
        ACTIVE_PARTICIPLE: participle("מa 10 2e ה", "מa 10 2ā ה", "מa 10 2"),
        INF_ABSOLUTE: inf("הa 10 2ē ה"),
        INF_CONSTRUCT: inf("הa 10 2ô ת"),
    },
    "H": {
        PERFECT: _iii_he_perfect("הå 10 2ā ה", "הå 10 2ê", "הå 10 2ə תā ה", "הå 10 2û"),
        IMPERFECT: imperfect("יå תå אå נå", "10 2e ה", "10 2", None),
        PASSIVE_PARTICIPLE: participle("מå 10 2e ה", "מå 10 2ā ה", "מå 10 2"),
    },
}

# Hollow verbs show a long vowel for their middle radical: qām, yāqûm, hēqîm
HOLLOW: dict[str, StemTables] = {
    "q": {
        PERFECT: perfect("1ā 3", "1ā 3", "1a 30"),
        IMPERFECT: imperfect("יā תā אā נā", "1{V} 3", "1{V} 3", None),
        JUSSIVE: jussive("יā תā אā נā", "1{Vj} 3"),
        COHORTATIVE: cohortative("יā תā אā נā", "1{V} 3ā ה"),
        IMPERATIVE: imperative("1{V} 3", "1{V} 3", None),
        ACTIVE_PARTICIPLE: participle("1ā 3", "1ā 3ā ה", "1ā 3"),
        INF_ABSOLUTE: inf("1ô 3"),
        INF_CONSTRUCT: inf("1{V} 3"),
    },
    "N": {
        PERFECT: perfect("נā 1ô 3", "נā 1ô 3", "נə 1û 3ô"),
        IMPERFECT: imperfect("יi תi אi נi", "1:ô 3", "1:ô 3", None),
        IMPERATIVE: imperative("הi 1:ô 3", "הi 1:ô 3", None),
        ACTIVE_PARTICIPLE: participle("נā 1ô 3", "נə 1ô 3ā ה", "נə 1ô 3"),
        INF_CONSTRUCT: inf("הi 1:ô 3"),
    },
    "h": {
        PERFECT: perfect("הē 1î 3", "הē 1î 3", "הē 1a 30"),
        IMPERFECT: imperfect("יā תā אā נā", "1î 3", "1î 3", None),
        JUSSIVE: jussive("יā תā אā נā", "1{J} 3"),
        COHORTATIVE: cohortative("יā תā אā נā", "1î 3ā ה"),
        IMPERATIVE: imperative("הā 1ē 3", "הā 1î 3", None),
        ACTIVE_PARTICIPLE: participle("מē 1î 3", "מə 1î 3ā ה", "מə 1î 3"),
        INF_ABSOLUTE: inf("הā 1ē 3"),
        INF_CONSTRUCT: inf("הā 1î 3"),
    },
    "H": {
        PERFECT: perfect("הû 1a 3", "הû 1ə 3", "הû 1a 30"),
        IMPERFECT: imperfect("יû תû אû נû", "1a 3", "1ə 3", None),
        PASSIVE_PARTICIPLE: participle("מû 1ā 3", "מû 1e 3e ת", "מû 1ā 3"),
    },
}

# Geminates contract their last two radicals: sabbôtā, yāsōb, hēsēb. Cells left out fall back to the strong
# verb, whose sābab and sōbēb they share.
GEMINATE: dict[str, StemTables] = {
    "q": {
        # Only the consonant endings differ from the strong verb: sābab, sābəbû, but sabbôtā
        PERFECT: {
            "2ms": "1a 2:ô תā",
            "2fs": "1a 2:ô ת",
            "1cs": "1a 2:ô תî",
            "2mp": "1a 2:ô תe ם",
            "2fp": "1a 2:ô תe ן",
            "1cp": "1a 2:ô נû",
        },
        IMPERFECT: imperfect("יā תā אā נā", "1o 2", "1o 2:", None),
        COHORTATIVE: cohortative("יā תā אā נā", "1o 2:ā ה"),
        IMPERATIVE: imperative("1o 2", "1o 2:", None),
        INF_CONSTRUCT: inf("1o 2"),
    },
    "N": {
        PERFECT: perfect("נā 1a 2", "נā 1a 2:", "נə 1a 2:ô"),
        IMPERFECT: imperfect("יi תi אi נi", "1:a 2", "1:a 2:", None),
        IMPERATIVE: imperative("הi 1:ē 2", "הi 1:ē 2:", None),
        ACTIVE_PARTICIPLE: participle("נā 1ā 2", "נə 1a 2:ā ה", "נə 1a 2:"),
        INF_CONSTRUCT: inf("הi 1:ē 2"),
    },
    "h": {
        PERFECT: perfect("הē 1ē 2", "הē 1ē 2:", "הă 1i 2:ô"),
        IMPERFECT: imperfect("יā תā אā נā", "1ē 2", "1ē 2:", None),
        IMPERATIVE: imperative("הā 1ē 2", "הā 1ē 2:", None),
        ACTIVE_PARTICIPLE: participle("מē 1ē 2", "מə 1i 2:ā ה", "מə 1i 2:"),
        INF_CONSTRUCT: inf("הā 1ē 2"),
    },
    "H": {
        PERFECT: perfect("הû 1a 2", "הû 1a 2:", "הû 1a 2:ô"),
        IMPERFECT: imperfect("יû תû אû נû", "1a 2", "1a 2:", None),
        PASSIVE_PARTICIPLE: participle("מû 1ā 2", "מû 1a 2:ā ה", "מû 1a 2:"),
    },
}
# Originally I-waw verbs lose the first radical in the Qal imperative and infinitive construct: šēb, šebet
DROPS_FIRST: StemTables = {
    IMPERATIVE: imperative("2{T} 3", "2ə 3", "2{T} 30 נā ה"),
    INF_CONSTRUCT: inf("2e 3e ת"),
}


def _layers(root: VerbRoot, stem: str, params: Params) -> list[StemTables]:
    """The tables to look a cell up in, most specific first. The last is complete: a cell it lacks has no form."""
    weak = root.weaknesses
    polel = stem in POLEL
    stem = POLEL.get(stem, stem)
    if Weakness.III_HE in weak:
        return [] if polel else [III_HE.get(stem, {})]
    if Weakness.HOLLOW in weak and not polel:
        return [HOLLOW.get(stem, {})]
    layers: list[StemTables] = []
    waw_first = (
        Weakness.I_YOD in weak
        and params.waw_original
        or "q" in root.irregular.first_like_waw
    )
    if stem == "q" and waw_first:
        layers.append(DROPS_FIRST)
    if Weakness.GEMINATE in weak and not polel:
        layers.append(GEMINATE.get(stem, {}))
    return [*layers, STRONG.get(stem, {})]


def template(
    root: VerbRoot, stem: str, typ: str, cell: str, params: Params
) -> Maybe[str]:
    """The template for one cell, layering the root's class tables over the strong verb's."""
    for tables in _layers(root, stem, params):
        # Only some persons have a short jussive; the rest are the imperfect's
        table = tables.get(JUSSIVE, {}) if typ == JUSSIVE else {}
        if cell not in table:
            table = tables.get(IMPERFECT if typ == JUSSIVE else typ, {})
        if cell in table:
            return table[cell]
    return None


_HOLLOW_JUSSIVE = {"û": "o", "ô": "o", "î": "ē"}
_HOLLOW_WAYYIQTOL = {"û": "ā", "ô": "o", "î": "e"}


def _vowels(root: VerbRoot, params: Params, wayyiqtol: bool) -> dict[str, str]:
    """The vowels the templates' placeholders stand for."""
    hollow = root.hollow.value if root.hollow else "û"
    return {
        # The Qal perfect's stem vowel, before a vowel and before a consonant ending: kābēd, kābadtā
        "P": root.perfect_theme,
        "Q": "o" if root.perfect_theme == "o" else "a",
        # The Qal imperfect's theme vowel: yišmōr, wayyēšeb
        "T": params.wayyiqtol_theme if wayyiqtol else params.imperfect_theme,
        # A hollow verb's long vowel, and its jussive: yāqûm, yāqōm, wayyāqom
        "V": hollow,
        "Vj": (_HOLLOW_WAYYIQTOL if wayyiqtol else _HOLLOW_JUSSIVE)[hollow],
        # The hollow Hiphil jussive: yāqēm, wayyāqem
        "J": "e" if wayyiqtol else "ē",
    }


def _polel(units: list[Unit], root: VerbRoot) -> None:
    # qômēm, sôbēb: a long ō after the first radical takes the place of the doubling
    for unit in units:
        if unit.radical == 1:
            unit.vowel = "ô"
        elif unit.radical == 2:
            unit.doubled = False
            if Weakness.HOLLOW in root.weaknesses:
                unit.radical = 3


def generate(
    root: VerbRoot, stem: str, typ: str, cell: str, params: Params = Params()
) -> Maybe[str]:
    """One pointed form, or None when the stem, conjugation or class is not covered."""
    if typ not in TYPES.get(stem, []) or cell not in CELLS[typ]:
        return None
    base_typ = typ
    if typ == SEQ_PERFECT:
        base_typ = PERFECT
    elif typ == SEQ_IMPERFECT:
        # wayyiqtol builds on the short jussive, except in the 1cs, which keeps the long form
        base_typ = IMPERFECT if cell == "1cs" else JUSSIVE
    found = template(root, stem, base_typ, cell, params)
    if not found:
        return None
    units = parse(found.format_map(_vowels(root, params, typ == SEQ_IMPERFECT)))
    if stem in POLEL:
        _polel(units, root)
    ctx = Context(root, POLEL.get(stem, stem), base_typ, params)
    units = apply_rules(units, ctx)
    if not units:
        return None
    if typ == SEQ_IMPERFECT:
        units = after_waw_consecutive(units)
    return spell(units)
