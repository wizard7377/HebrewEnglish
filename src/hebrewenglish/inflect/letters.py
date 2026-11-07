"""Hebrew letters, points, and the normalisation used to compare generated forms with attested ones."""

import unicodedata

SHEWA = "ְ"
HATEF_SEGOL = "ֱ"
HATEF_PATAH = "ֲ"
HATEF_QAMATS = "ֳ"
HIRIQ = "ִ"
TSERE = "ֵ"
SEGOL = "ֶ"
PATAH = "ַ"
QAMATS = "ָ"
HOLAM = "ֹ"
HOLAM_HASER_FOR_VAV = "ֺ"
QIBBUTS = "ֻ"
DAGESH = "ּ"
METEG = "ֽ"
MAQAF = "־"
RAFE = "ֿ"
SHIN_DOT = "ׁ"
SIN_DOT = "ׂ"
QAMATS_QATAN = "ׇ"

VOWELS = frozenset(
    [
        SHEWA,
        HATEF_SEGOL,
        HATEF_PATAH,
        HATEF_QAMATS,
        HIRIQ,
        TSERE,
        SEGOL,
        PATAH,
        QAMATS,
        HOLAM,
        QIBBUTS,
    ]
)

GUTTURALS = frozenset("אהחע")
# Resh refuses doubling like a guttural but otherwise behaves as an ordinary consonant
NO_DOUBLING = GUTTURALS | {"ר"}
BEGADKEFAT = frozenset("בגדכפת")
SIBILANTS = frozenset("סשצז")

FINAL_FORMS = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}
MEDIAL_FORMS = {final: medial for medial, final in FINAL_FORMS.items()}


def clusters(value: str) -> list[str]:
    """Split pointed Hebrew (NFD) into letters, each carrying its own points."""
    result: list[str] = []
    for character in unicodedata.normalize("NFD", value):
        if unicodedata.category(character).startswith("M") and result:
            result[-1] += character
        else:
            result.append(character)
    return result


def base(cluster: str) -> str:
    """The bare letter of a cluster, in its medial form."""
    return MEDIAL_FORMS.get(cluster[:1], cluster[:1])


def letter(cluster: str) -> str:
    """The letter with its shin or sin dot but no vowels or dagesh, in its medial form."""
    return base(cluster) + "".join(c for c in cluster[1:] if c in (SHIN_DOT, SIN_DOT))


def has_vowel(cluster: str) -> bool:
    return any(c in VOWELS and c != SHEWA for c in cluster)


def _is_accent(character: str) -> bool:
    return "֑" <= character <= "֯" or character in (METEG, RAFE, "׀", "׃", "ׄ", "ׅ")


def comparable(form: str) -> str:
    """Fold away what varies between copies of one form, so a generated form can be matched against attestations.

    Drops accents and meteg; the dagesh lene of a first letter or of a letter after shewa, which depends on what
    the OSHB writes apart before it; and matres lectionis, so that plene and defective spellings compare equal.
    """
    text = unicodedata.normalize("NFD", form)
    text = text.replace(HOLAM_HASER_FOR_VAV, HOLAM).replace(QAMATS_QATAN, QAMATS)
    text = "".join(c for c in text if not _is_accent(c) and c not in (MAQAF, "/"))
    parts = clusters(text)
    if parts and base(parts[0]) in BEGADKEFAT:
        parts[0] = parts[0].replace(DAGESH, "")
    folded: list[str] = []
    for cluster in parts:
        previous = folded[-1] if folded else None
        marks = cluster[1:]
        bare_previous = (
            previous is not None and not has_vowel(previous) and SHEWA not in previous
        )
        if base(cluster) == "ו" and bare_previous and marks in (HOLAM, DAGESH):
            folded[-1] = previous + (HOLAM if marks == HOLAM else QIBBUTS)
            continue
        if (
            base(cluster) == "י"
            and not marks
            and previous is not None
            and (HIRIQ in previous or TSERE in previous)
        ):
            continue
        if base(cluster) in BEGADKEFAT and previous is not None and SHEWA in previous:
            # Whether that shewa is silent depends on a prefix the OSHB writes apart: bəgōd, but liḇgōd
            cluster = cluster.replace(DAGESH, "")
        folded.append(cluster)
    return unicodedata.normalize("NFC", "".join(folded))


# The short vowel the conjunction takes before each hatef: wa'ăšer, we'ĕmōr, wā'ŏnî
_HATEF_VOWELS = {HATEF_PATAH: PATAH, HATEF_SEGOL: SEGOL, HATEF_QAMATS: QAMATS}


def with_conjunction(form: str, consecutive: bool = False) -> str:
    """A verb form with the ו that the OSHB writes apart from it.

    A wayyiqtol takes וַ, or וָ before the 1cs aleph; its doubled prefix is already in the form. Any other form
    takes וְ, which becomes וּ before a labial or a shewa, וִ before yod with shewa (whose shewa it absorbs), and
    the matching short vowel before a hatef. After the conjunction's vowel a begadkefat loses its dagesh lene.
    """
    parts = clusters(form)
    if not parts:
        return form
    first = parts[0]
    hatef = next((mark for mark in first if mark in _HATEF_VOWELS), None)
    if consecutive:
        prefix = "ו" + (QAMATS if base(first) == "א" else PATAH)
    elif base(first) == "י" and SHEWA in first:
        prefix, parts[0] = "ו" + HIRIQ, first.replace(SHEWA, "")
    elif SHEWA in first or base(first) in "במפ":
        prefix = "ו" + DAGESH
    elif hatef is not None:
        prefix = "ו" + _HATEF_VOWELS[hatef]
    else:
        prefix = "ו" + SHEWA
    if not consecutive and base(first) in BEGADKEFAT:
        parts[0] = parts[0].replace(DAGESH, "", 1)
    return unicodedata.normalize("NFC", prefix + "".join(parts))
