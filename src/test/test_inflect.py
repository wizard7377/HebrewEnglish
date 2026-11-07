import unicodedata
from collections import Counter

import pytest

from hebrewenglish.inflect.evaluate import load_verbs, trials
from hebrewenglish.inflect.generate import Slot, default_params, fit, reconstruct
from hebrewenglish.inflect.letters import comparable, with_conjunction
from hebrewenglish.inflect.paradigm import generate
from hebrewenglish.inflect.roots import Hollow, Weakness, verb_root


def nfc(text):
    return unicodedata.normalize("NFC", text)


def forms(root, lemma, *cells):
    verb = verb_root(root, lemma)
    params = default_params(verb)
    return [generate(verb, stem, typ, cell, params) for stem, typ, cell in cells]


PERFECT = ["3ms", "3fs", "2ms", "2fs", "1cs", "3cp", "2mp", "2fp", "1cp"]


def test_shamar_qal_perfect():
    assert forms("שׁמר", "שָׁמַר", *(("q", "p", cell) for cell in PERFECT)) == [
        nfc(f)
        for f in [
            "שָׁמַר",
            "שָׁמְרָה",
            "שָׁמַרְתָּ",
            "שָׁמַרְתְּ",
            "שָׁמַרְתִּי",
            "שָׁמְרוּ",
            "שְׁמַרְתֶּם",
            "שְׁמַרְתֶּן",
            "שָׁמַרְנוּ",
        ]
    ]


def test_shamar_qal_imperfect_and_imperative():
    cells = [("q", "i", c) for c in ["3ms", "2fs", "1cs", "3mp", "3fp"]] + [
        ("q", "v", c) for c in ["2ms", "2fs", "2fp"]
    ]
    assert forms("שׁמר", "שָׁמַר", *cells) == [
        nfc(f)
        for f in ["יִשְׁמֹר", "תִּשְׁמְרִי", "אֶשְׁמֹר", "יִשְׁמְרוּ", "תִּשְׁמֹרְנָה", "שְׁמֹר", "שִׁמְרִי", "שְׁמֹרְנָה"]
    ]


def test_shamar_derived_stems():
    cells = [
        ("N", "p", "3ms"),
        ("N", "i", "3ms"),
        ("p", "p", "3ms"),
        ("h", "p", "3ms"),
        ("t", "p", "3ms"),
    ]
    assert forms("שׁמר", "שָׁמַר", *cells) == [
        nfc(f) for f in ["נִשְׁמַר", "יִשָּׁמֵר", "שִׁמֵּר", "הִשְׁמִיר", "הִשְׁתַּמֵּר"]
    ]


def test_participles_and_infinitives():
    cells = [
        ("q", "r", "ms"),
        ("q", "r", "fs"),
        ("q", "s", "ms"),
        ("q", "a", ""),
        ("q", "c", ""),
    ]
    assert forms("שׁמר", "שָׁמַר", *cells) == [
        nfc(f) for f in ["שֹׁמֵר", "שֹׁמֶרֶת", "שָׁמוּר", "שָׁמֹר", "שְׁמֹר"]
    ]


# The wayyiqtol's waw is a separate OSHB segment, so the form keeps only the doubling it causes
@pytest.mark.parametrize(
    "root, lemma, cells, expected",
    [
        (
            "עמד",
            "עָמַד",
            [("q", "i", "3ms"), ("N", "p", "3ms"), ("h", "p", "3ms")],
            ["יַעֲמֹד", "נֶעֱמַד", "הֶעֱמִיד"],
        ),
        (
            "שׁמע",
            "שָׁמַע",
            [("q", "i", "3ms"), ("q", "r", "ms"), ("h", "p", "3ms")],
            ["יִשְׁמַע", "שֹׁמֵעַ", "הִשְׁמִיעַ"],
        ),
        (
            "מצא",
            "מָצָא",
            [("q", "p", "3ms"), ("q", "p", "2ms"), ("q", "i", "3ms")],
            ["מָצָא", "מָצָאתָ", "יִמְצָא"],
        ),
        (
            "נפל",
            "נָפַל",
            [("q", "i", "3ms"), ("N", "p", "3ms"), ("h", "p", "3ms")],
            ["יִפֹּל", "נִפַּל", "הִפִּיל"],
        ),
        (
            "ישׁב",
            "יָשַׁב",
            [
                ("q", "i", "3ms"),
                ("q", "v", "2ms"),
                ("q", "c", ""),
                ("N", "p", "3ms"),
                ("h", "p", "3ms"),
            ],
            ["יֵשֵׁב", "שֵׁב", "שֶׁבֶת", "נוֹשַׁב", "הוֹשִׁיב"],
        ),
        (
            "בנה",
            "בָּנָה",
            [
                ("q", "p", "3ms"),
                ("q", "i", "3ms"),
                ("q", "w", "3ms"),
                ("q", "c", ""),
                ("q", "r", "ms"),
            ],
            ["בָּנָה", "יִבְנֶה", "יִּבֶן", "בְּנוֹת", "בֹּנֶה"],
        ),
        (
            "קום",
            "קוּם",
            [
                ("q", "p", "3ms"),
                ("q", "i", "3ms"),
                ("q", "v", "2ms"),
                ("N", "p", "3ms"),
                ("h", "p", "3ms"),
            ],
            ["קָם", "יָקוּם", "קוּם", "נָקוֹם", "הֵקִים"],
        ),
        (
            "סבב",
            "סָבַב",
            [("q", "p", "3ms"), ("q", "i", "3ms"), ("h", "p", "3ms")],
            ["סָבַב", "יָסֹב", "הֵסֵב"],
        ),
        (
            "נטה",
            "נָטָה",
            [("q", "i", "3ms"), ("q", "w", "3ms"), ("h", "w", "3ms")],
            ["יִטֶּה", "יֵּט", "יַּט"],
        ),
    ],
)
def test_weak_classes(root, lemma, cells, expected):
    assert forms(root, lemma, *cells) == [nfc(f) for f in expected]


def test_comparable_folds_spelling_variants():
    # Plene and defective spellings, and the dagesh lene a preceding word removes
    assert comparable("שׁוֹמֵר") == comparable("שֹׁמֵר")
    assert comparable("הִשְׁמִיר") == comparable("הִשְׁמִר")
    assert comparable("בְּגֹד") == comparable("בְגֹּד")
    assert comparable("שָׁמַר") != comparable("שָׁמָר")


@pytest.mark.parametrize(
    "form, consecutive, expected",
    [
        ("שָׁמַרְתָּ", False, "וְשָׁמַרְתָּ"),
        ("בָּנִיתָ", False, "וּבָנִיתָ"),
        ("שְׁמַרְתֶּם", False, "וּשְׁמַרְתֶּם"),
        ("יְדַעְתֶּם", False, "וִידַעְתֶּם"),
        ("אֲכַלְתֶּם", False, "וַאֲכַלְתֶּם"),
        ("דִּבֵּר", False, "וְדִבֵּר"),
        ("יִּשְׁמֹר", True, "וַיִּשְׁמֹר"),
        ("אֶשְׁמֹר", True, "וָאֶשְׁמֹר"),
    ],
)
def test_conjunction_takes_the_vowel_its_form_needs(form, consecutive, expected):
    assert with_conjunction(form, consecutive) == unicodedata.normalize("NFC", expected)


def test_verb_root_classes():
    assert verb_root("שׁמר", "שָׁמַר").label == "Strong"
    assert verb_root("בנה", "בָּנָה").weaknesses == {Weakness.III_HE}
    assert verb_root("גבה", "גָּבַהּ").weaknesses == {Weakness.III_GUTTURAL}
    qum = verb_root(None, "קוּם")
    assert qum.hollow is Hollow.U and qum.letters[1] == "ו"
    # A waw with its own vowel is a consonant, not a hollow root's mater
    assert verb_root("גוע", "גָּוַע").hollow is None
    assert verb_root("אמר", "אָמַר").label == "I-aleph"
    assert verb_root("כבד", "כָּבֵד").perfect_theme == "ē"
    assert verb_root(None, "כִּסֵּא") is not None
    assert verb_root(None, "כָּרְסֵם") is None


def test_fit_reads_the_imperfect_theme_from_attested_forms():
    lamad = verb_root("למד", "לָמַד")
    attested = {Slot("q", "i", "3ms"): ["יִלְמַד"], Slot("q", "i", "3mp"): ["יִלְמְדוּ"]}
    assert fit(lamad, "q", attested).imperfect_theme == "a"
    assert fit(lamad, "q", {}).imperfect_theme == "o"


def test_reconstruct_fills_only_the_gaps():
    shamar = verb_root("שׁמר", "שָׁמַר")
    filled = reconstruct(shamar, "q", {Slot("q", "p", "3ms"): ["שָׁמַר"]})
    assert Slot("q", "p", "3ms") not in filled
    assert filled[Slot("q", "p", "2fp")] == nfc("שְׁמַרְתֶּן")
    assert all(slot.stem == "q" for slot in filled)


def test_accuracy_gate():
    hits: Counter[str] = Counter()
    for trial in trials(load_verbs()):
        strong_qal = trial.verb.root.label == "Strong" and trial.slot.stem == "q"
        for bucket in ("all", "strong-qal") if strong_qal else ("all",):
            hits[bucket + "-cells"] += 1
            hits[bucket] += trial.matches(trial.fitted)
    # Most misses left are pausal forms and lexical variants (qittel beside qittal), not rule failures
    assert hits["strong-qal"] / hits["strong-qal-cells"] >= 0.87
    assert hits["all"] / hits["all-cells"] >= 0.77
