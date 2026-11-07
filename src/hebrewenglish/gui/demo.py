"""Demonstration lexicon from the Figma Make prototype, used until the backend can supply results."""

from hebrewenglish.gui.model import (
    Attestation,
    Category,
    LexicalResult,
    MorphologyGroup,
    MorphologyRow,
    Property,
    ResolvedForm,
    SuffixId,
)
from hebrewenglish.lexicon.similar import consonants, skeleton

SUPPORTED_QUERIES = ["guard", "keep", "watch", "preserve"]
RELATED_TERMS = ["guard", "keep", "watch"]
HEBREW_TERMS = ["שמר", "משמרת", "נטר"]


def _attested(
    base: str, suffix: str, form: str, transliteration: str, *references: str
) -> ResolvedForm:
    return ResolvedForm(
        base, suffix, form, transliteration, Attestation.ATTESTED, references
    )


_SHAMAR_SUFFIXED = {
    ("שְׁמֹר", SuffixId.P1CS): _attested("שָׁמְרֵ", "נִי", "שָׁמְרֵנִי", "šomrēnî", "Psalm 16:1"),
    ("יִשְׁמֹר", SuffixId.P2MS): _attested("יִשְׁמָרְ", "ךָ", "יִשְׁמָרְךָ", "yišmorkā", "Psalm 121:7"),
}

_MISHMERET_SUFFIXED = {
    ("מִשְׁמֶרֶת", SuffixId.P1CS): _attested(
        "מִשְׁמַרְתִּ", "י", "מִשְׁמַרְתִּי", "mišmartî", "Leviticus 22:9"
    ),
}

# לְ contracts with every pronominal suffix into a single attested form
_LE_SUFFIXED = {
    ("לְ", suffix_id): _attested(base, suffix, form, transliteration, *references)
    for suffix_id, base, suffix, form, transliteration, references in [
        (SuffixId.P1CS, "לִ", "י", "לִי", "lî", ("Genesis 29:15", "Psalm 119:92")),
        (SuffixId.P2MS, "לְ", "ךָ", "לְךָ", "ləkā", ("Genesis 12:1", "Psalm 119:105")),
        (SuffixId.P2FS, "לָ", "ךְ", "לָךְ", "lāk", ("Ruth 1:15", "Isaiah 54:4")),
        (SuffixId.P3MS, "ל", "וֹ", "לוֹ", "lô", ("Genesis 3:21", "Psalm 32:1")),
        (SuffixId.P3FS, "לָ", "הּ", "לָהּ", "lāh", ("Genesis 16:1", "Ruth 4:13")),
        (SuffixId.P1CP, "לָ", "נוּ", "לָנוּ", "lānû", ("Genesis 47:15", "Joshua 24:18")),
        (SuffixId.P2MP, "לָ", "כֶם", "לָכֶם", "lākem", ("Genesis 45:20", "Exodus 12:27")),
        (SuffixId.P2FP, "לָ", "כֶן", "לָכֶן", "lāken", ("Exodus 1:19", "Ruth 1:8")),
        (SuffixId.P3MP, "לָ", "הֶם", "לָהֶם", "lāhem", ("Genesis 11:3", "Exodus 14:28")),
        (SuffixId.P3FP, "לָ", "הֶן", "לָהֶן", "lāhen", ("Exodus 1:19", "Ezekiel 16:44")),
    ]
}

LEXICAL_RESULTS: list[LexicalResult] = [
    LexicalResult(
        id="verb-shamar",
        part_of_speech="Verb",
        category=Category.HEBREW,
        lemma="שָׁמַר",
        transliteration="šāmar",
        short_definition="to keep, guard, observe, or watch over",
        long_definition=(
            "A broad verb of careful attention: to guard a person or place, "
            "preserve something entrusted, observe a command, or keep watch. "
            "Context determines whether the emphasis is physical protection, "
            "covenant faithfulness, or attentive obedience."
        ),
        properties=[
            Property("Root", "שׁמר", hebrew=True),
            Property("Language", "Hebrew"),
            Property("Stem", "Qal"),
            Property("Root class", "Strong"),
            Property("Lexicon no.", "H8104"),
        ],
        morphology=[
            MorphologyGroup(
                id="perfect",
                label="Perfect",
                description="Completed action, commonly narrated as a whole.",
                rows=[
                    MorphologyRow(
                        label="3rd masc. singular",
                        note="he",
                        form="שָׁמַר",
                        transliteration="šāmar",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 2:15", "1 Samuel 21:5"),
                    ),
                    MorphologyRow(
                        label="3rd fem. singular",
                        note="she",
                        form="שָׁמְרָה",
                        transliteration="šāmrâ",
                        attestation=Attestation.ATTESTED,
                        references=("Psalm 119:167",),
                    ),
                    MorphologyRow(
                        label="2nd masc. singular",
                        note="you",
                        form="שָׁמַרְתָּ",
                        transliteration="šāmartā",
                        attestation=Attestation.ATTESTED,
                        references=("1 Kings 8:24",),
                    ),
                    MorphologyRow(
                        label="2nd fem. singular",
                        note="you",
                        form="שָׁמַרְתְּ",
                        transliteration="šāmart",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="2nd masc. plural",
                        note="you all",
                        form="שְׁמַרְתֶּם",
                        transliteration="šəmartem",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="2nd fem. plural",
                        note="you all",
                        form="שְׁמַרְתֶּן",
                        transliteration="šəmarten",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="1st common singular",
                        note="I",
                        form="שָׁמַרְתִּי",
                        transliteration="šāmartî",
                        alternative="שָׁמַרְתִּ",
                        attestation=Attestation.ATTESTED,
                        references=("Psalm 17:4",),
                    ),
                    MorphologyRow(
                        label="3rd common plural",
                        note="they",
                        form="שָׁמְרוּ",
                        transliteration="šāmrû",
                        attestation=Attestation.ATTESTED,
                        references=("Psalm 105:45",),
                    ),
                    MorphologyRow(
                        label="1st common plural",
                        note="we",
                        form="שָׁמַרְנוּ",
                        transliteration="šāmarnû",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
            MorphologyGroup(
                id="imperfect",
                label="Imperfect",
                description="Incomplete, habitual, modal, or future-oriented action.",
                rows=[
                    MorphologyRow(
                        label="3rd masc. singular",
                        note="he",
                        form="יִשְׁמֹר",
                        transliteration="yišmōr",
                        alternative="יִשְׁמוֹר",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 28:20", "Psalm 121:7"),
                    ),
                    MorphologyRow(
                        label="3rd fem. singular",
                        note="she",
                        form="תִּשְׁמֹר",
                        transliteration="tišmōr",
                        attestation=Attestation.ATTESTED,
                        references=("Exodus 23:13", "Deuteronomy 8:11"),
                    ),
                    MorphologyRow(
                        label="3rd masc. plural",
                        note="they",
                        form="יִשְׁמְרוּ",
                        transliteration="yišmərû",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="3rd fem. plural",
                        note="they",
                        form="תִּשְׁמֹרְנָה",
                        transliteration="tišmōrnâ",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="2nd masc. singular",
                        note="you",
                        form="תִּשְׁמֹר",
                        transliteration="tišmōr",
                        attestation=Attestation.ATTESTED,
                        references=("Exodus 23:13", "Deuteronomy 8:11"),
                    ),
                    MorphologyRow(
                        label="2nd fem. singular",
                        note="you",
                        form="תִּשְׁמְרִי",
                        transliteration="tišmərî",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="2nd masc. plural",
                        note="you all",
                        form="תִּשְׁמְרוּ",
                        transliteration="tišmərû",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="2nd fem. plural",
                        note="you all",
                        form="תִּשְׁמֹרְנָה",
                        transliteration="tišmōrnâ",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="1st common singular",
                        note="I",
                        form="אֶשְׁמֹר",
                        transliteration="ʾešmōr",
                        attestation=Attestation.ATTESTED,
                        references=("Psalm 39:2",),
                    ),
                    MorphologyRow(
                        label="1st common plural",
                        note="we",
                        form="נִשְׁמֹר",
                        transliteration="nišmōr",
                        attestation=Attestation.ATTESTED,
                        references=("Nehemiah 10:30",),
                    ),
                ],
            ),
            MorphologyGroup(
                id="imperative",
                label="Imperative",
                description="Direct commands addressed to a second person.",
                rows=[
                    MorphologyRow(
                        label="Masculine singular",
                        note="you",
                        form="שְׁמֹר",
                        transliteration="šəmōr",
                        alternative="שָׁמְרָה",
                        attestation=Attestation.ATTESTED,
                        references=("Exodus 34:11", "Deuteronomy 5:12"),
                    ),
                    MorphologyRow(
                        label="Feminine singular",
                        note="you",
                        form="שִׁמְרִי",
                        transliteration="šimrî",
                        attestation=Attestation.ATTESTED,
                        references=("Ecclesiastes 4:17",),
                    ),
                    MorphologyRow(
                        label="Masculine plural",
                        note="you all",
                        form="שִׁמְרוּ",
                        transliteration="šimrû",
                        attestation=Attestation.ATTESTED,
                        references=("Psalm 31:24",),
                    ),
                    MorphologyRow(
                        label="Feminine plural",
                        note="you all",
                        form="שְׁמֹרְנָה",
                        transliteration="šəmōrnâ",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
            MorphologyGroup(
                id="participle",
                label="Participle",
                description="Ongoing activity or the characteristic role of a keeper.",
                rows=[
                    MorphologyRow(
                        label="Masculine singular",
                        form="שֹׁמֵר",
                        transliteration="šōmēr",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 4:9", "Psalm 121:4"),
                    ),
                    MorphologyRow(
                        label="Feminine singular",
                        form="שֹׁמֶרֶת",
                        transliteration="šōmeret",
                        attestation=Attestation.ATTESTED,
                        references=("1 Samuel 25:21",),
                    ),
                    MorphologyRow(
                        label="Masculine plural",
                        form="שֹׁמְרִים",
                        transliteration="šōmərîm",
                        attestation=Attestation.ATTESTED,
                        references=("1 Samuel 22:4", "Nehemiah 12:25"),
                    ),
                    MorphologyRow(
                        label="Feminine plural",
                        form="שֹׁמְרוֹת",
                        transliteration="šōmərôt",
                        attestation=Attestation.ATTESTED,
                        references=("Song of Songs 5:7",),
                    ),
                ],
            ),
        ],
        suffixed_forms=_SHAMAR_SUFFIXED,
    ),
    LexicalResult(
        id="noun-mishmeret",
        part_of_speech="Noun",
        category=Category.HEBREW,
        lemma="מִשְׁמֶרֶת",
        transliteration="mišmeret",
        short_definition="a charge, watch, duty, or obligation to be kept",
        long_definition=(
            "A feminine noun for what is placed under guard or entrusted for "
            "observance. It can describe a watch-post, a priestly duty, a "
            "divine ordinance, or the responsibility of preserving something "
            "committed to one’s care."
        ),
        properties=[
            Property("Root", "שׁמר", hebrew=True),
            Property("Language", "Hebrew"),
            Property("Gender", "Feminine"),
            Property("Pattern", "miqtélet"),
            Property("Lexicon no.", "H4931"),
        ],
        morphology=[
            MorphologyGroup(
                id="absolute",
                label="Absolute",
                description="Independent noun forms, not bound to a following noun.",
                rows=[
                    MorphologyRow(
                        label="Singular",
                        form="מִשְׁמֶרֶת",
                        transliteration="mišmeret",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 26:5", "Numbers 1:53"),
                    ),
                    MorphologyRow(
                        label="Plural",
                        form="מִשְׁמָרוֹת",
                        transliteration="mišmārôt",
                        alternative="מִשְׁמְרוֹת",
                        attestation=Attestation.ATTESTED,
                        references=("Nehemiah 12:24", "Ezekiel 44:8"),
                    ),
                ],
            ),
            MorphologyGroup(
                id="construct",
                label="Construct",
                description="Bound forms completed by a following possessor.",
                rows=[
                    MorphologyRow(
                        label="Singular construct",
                        form="מִשְׁמֶרֶת",
                        transliteration="mišmeret",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 26:5", "Numbers 1:53"),
                    ),
                    MorphologyRow(
                        label="Plural construct",
                        form="מִשְׁמְרוֹת",
                        transliteration="mišmərôt",
                        attestation=Attestation.ATTESTED,
                        references=("Nehemiah 13:30",),
                    ),
                ],
            ),
            MorphologyGroup(
                id="suffixes",
                label="With suffixes",
                description="Selected forms carrying a pronominal possessor.",
                rows=[
                    MorphologyRow(
                        label="1st common singular",
                        note="my charge",
                        form="מִשְׁמַרְתִּי",
                        transliteration="mišmartî",
                        attestation=Attestation.ATTESTED,
                        references=("Leviticus 22:9",),
                    ),
                    MorphologyRow(
                        label="2nd masc. singular",
                        note="your charge",
                        form="מִשְׁמַרְתְּךָ",
                        transliteration="mišmartəkā",
                        attestation=Attestation.ATTESTED,
                        references=("1 Kings 2:3",),
                    ),
                    MorphologyRow(
                        label="3rd masc. singular",
                        note="his charge",
                        form="מִשְׁמַרְתּוֹ",
                        transliteration="mišmartô",
                        attestation=Attestation.ATTESTED,
                        references=("Numbers 3:7",),
                    ),
                    MorphologyRow(
                        label="3rd fem. plural",
                        note="their charge",
                        form="מִשְׁמַרְתָּן",
                        transliteration="mišmartān",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
        ],
        suffixed_forms=_MISHMERET_SUFFIXED,
    ),
    LexicalResult(
        id="adjective-shamur",
        part_of_speech="Adjective",
        category=Category.HEBREW,
        lemma="שָׁמוּר",
        transliteration="šāmûr",
        short_definition="kept, guarded, protected, or preserved",
        long_definition=(
            "A passive descriptive form from the root שׁמר. It characterizes "
            "a person or thing as guarded or preserved, drawing attention to "
            "the resulting state rather than to the act of guarding itself."
        ),
        properties=[
            Property("Root", "שׁמר", hebrew=True),
            Property("Language", "Hebrew"),
            Property("Formation", "Qal passive"),
            Property("Agreement", "Gender + no."),
            Property("Lexical class", "Verbal adj."),
        ],
        morphology=[
            MorphologyGroup(
                id="positive",
                label="Positive forms",
                description="Regular agreement forms used attributively or predicatively.",
                rows=[
                    MorphologyRow(
                        label="Masculine singular",
                        form="שָׁמוּר",
                        transliteration="šāmûr",
                        attestation=Attestation.ATTESTED,
                        references=("Hosea 13:12",),
                    ),
                    MorphologyRow(
                        label="Feminine singular",
                        form="שְׁמוּרָה",
                        transliteration="šəmûrâ",
                        attestation=Attestation.ATTESTED,
                        references=("1 Samuel 9:24",),
                    ),
                    MorphologyRow(
                        label="Masculine plural",
                        form="שְׁמוּרִים",
                        transliteration="šəmûrîm",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="Feminine plural",
                        form="שְׁמוּרוֹת",
                        transliteration="šəmûrôt",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
            MorphologyGroup(
                id="definite",
                label="Definite forms",
                description="Forms shown with the prefixed definite article.",
                rows=[
                    MorphologyRow(
                        label="Masculine singular",
                        form="הַשָּׁמוּר",
                        transliteration="haššāmûr",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="Feminine singular",
                        form="הַשְּׁמוּרָה",
                        transliteration="haššəmûrâ",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
        ],
    ),
    LexicalResult(
        id="aramaic-netar",
        part_of_speech="Verb",
        category=Category.ARAMAIC,
        category_label="Aramaic",
        lemma="נְטַר",
        transliteration="nəṭar",
        short_definition="to keep or retain; an Aramaic cognate concept",
        long_definition=(
            "A native Aramaic verb expressing keeping or retaining. It is "
            "included as a comparative lexical possibility when searching the "
            "Aramaic portions and cognate vocabulary of the biblical corpus."
        ),
        properties=[
            Property("Root", "נטר", hebrew=True),
            Property("Language", "Aramaic"),
            Property("Stem", "Peal"),
            Property("Root class", "Strong"),
            Property("Scope", "Comparative"),
        ],
        morphology=[
            MorphologyGroup(
                id="peal-perfect",
                label="Peal perfect",
                description="Selected completed-action forms in the basic Aramaic stem.",
                rows=[
                    MorphologyRow(
                        label="3rd masc. singular",
                        form="נְטַר",
                        transliteration="nəṭar",
                        attestation=Attestation.ATTESTED,
                        references=("Daniel 7:28",),
                    ),
                    MorphologyRow(
                        label="3rd fem. singular",
                        form="נִטְרַת",
                        transliteration="niṭrat",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="3rd masc. plural",
                        form="נְטַרוּ",
                        transliteration="nəṭarû",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
            MorphologyGroup(
                id="peal-participle",
                label="Peal participle",
                description="Selected active participial forms.",
                rows=[
                    MorphologyRow(
                        label="Masculine singular",
                        form="נָטַר",
                        transliteration="nāṭar",
                        attestation=Attestation.UNATTESTED,
                    ),
                    MorphologyRow(
                        label="Masculine plural",
                        form="נָטְרִין",
                        transliteration="nāṭrîn",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
        ],
    ),
    LexicalResult(
        id="preposition-le",
        part_of_speech="Preposition",
        category=Category.PREPOSITION,
        category_label="Supplement",
        lemma="לְ",
        transliteration="lə",
        short_definition="to, for, or belonging to; contracts with pronominal suffixes",
        long_definition=(
            "A highly frequent inseparable preposition expressing direction, "
            "purpose, possession, or relationship. With pronominal suffixes "
            "it contracts into a single phonological and written form."
        ),
        properties=[
            Property("Base", "ל", hebrew=True),
            Property("Language", "Hebrew"),
            Property("Class", "Inseparable prep."),
            Property("Construction", "Proclitic"),
            Property("Lexicon no.", "H3807"),
        ],
        morphology=[
            MorphologyGroup(
                id="pronominal-contraction",
                label="Pronominal forms",
                description="The preposition contracts with a selected pronominal complement.",
                rows=[
                    MorphologyRow(
                        label="Base form",
                        form="לְ",
                        transliteration="lə",
                        attestation=Attestation.ATTESTED,
                        references=("Genesis 2:18", "Genesis 12:1"),
                    ),
                ],
            ),
        ],
        suffixed_forms=_LE_SUFFIXED,
    ),
    LexicalResult(
        id="proper-shemer",
        part_of_speech="Proper name",
        category=Category.PROPER_NAME,
        category_label="Name",
        lemma="שֶׁמֶר",
        transliteration="Šemer",
        short_definition="Shemer, a personal name associated with the root “guard”",
        long_definition=(
            "A masculine personal name traditionally connected with the "
            "consonantal root שׁמר. Proper names preserve lexical "
            "associations but should not be treated as ordinary inflected "
            "vocabulary."
        ),
        properties=[
            Property("Root", "שׁמר", hebrew=True),
            Property("Language", "Hebrew"),
            Property("Type", "Personal name"),
            Property("Gender", "Masculine"),
            Property("Lexicon no.", "H8106"),
        ],
        morphology=[
            MorphologyGroup(
                id="name-forms",
                label="Name forms",
                description="The attested name and a reconstructed prefixed form.",
                rows=[
                    MorphologyRow(
                        label="Unprefixed",
                        form="שֶׁמֶר",
                        transliteration="Šemer",
                        attestation=Attestation.ATTESTED,
                        references=("1 Chronicles 6:31", "1 Chronicles 7:34"),
                    ),
                    MorphologyRow(
                        label="With preposition",
                        note="to Shemer",
                        form="לְשֶׁמֶר",
                        transliteration="ləŠemer",
                        attestation=Attestation.UNATTESTED,
                    ),
                ],
            ),
        ],
    ),
]


def lookup(query: str) -> list[LexicalResult]:
    """Return the demonstration results for a supported English query, ordered by relevance."""
    return LEXICAL_RESULTS if query.strip().lower() in SUPPORTED_QUERIES else []


def hebrew_lookup(query: str) -> list[LexicalResult]:
    """Return the demonstration results spelled like a Hebrew word, ignoring points and plene spelling."""
    letters = skeleton(consonants(query))
    if not letters:
        return []
    return [result for result in LEXICAL_RESULTS if letters in skeleton(consonants(result.lemma))]
