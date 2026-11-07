import pytest

from hebrewenglish.lexicon.matcher import LexicalElement
from hebrewenglish.lexicon.res import (
    STRONG,
    STRONG_ELEMENTS,
    STRONG_GLOSSES,
    STRONG_LEXICON,
    StrongLexiconEntry,
    get_resource_path,
    index_glosses,
    json_to_strong_lexicon,
    json_to_strong_lexicon_entry,
    load_json_resource,
    parse_usage,
    strong_to_lexical_element,
)

ENTRY_JSON = {
    "id": "H1",
    "lemma": "אָב",
    "xlit": "ʼâb",
    "pron": "awb",
    "pos": "n-m",
    "lang": "heb",
    "source": "a primitive word;",
    "meaning": "father",
    "defs": ["father"],
    "usage": "chief",
    "see": ["H2"],
}


def test_get_resource_path_finds_a_resource():
    assert get_resource_path("strong.json").is_file()


def test_load_json_resource_parses_the_file():
    assert load_json_resource("strong.json") == STRONG


def test_entry_keeps_every_field():
    assert json_to_strong_lexicon_entry(ENTRY_JSON) == StrongLexiconEntry(**ENTRY_JSON)


def test_entry_fills_in_missing_fields():
    entry = json_to_strong_lexicon_entry({"id": "H1"})

    assert entry.id == "H1"
    assert entry.meaning == ""
    assert entry.defs == []
    assert entry.see == []


def test_lexicon_keeps_the_entry_ids():
    lexicon = json_to_strong_lexicon({"H1": ENTRY_JSON})

    assert lexicon.entries == {"H1": StrongLexiconEntry(**ENTRY_JSON)}


def test_strong_lexicon_has_every_entry():
    assert STRONG_LEXICON.entries.keys() == STRONG.keys()


def test_strong_lexicon_entries_are_stored_under_their_ids():
    assert all(key == entry.id for key, entry in STRONG_LEXICON.entries.items())


def test_strong_lexicon_reads_a_known_entry():
    entry = STRONG_LEXICON.entries["H1"]

    assert entry.lemma == "אָב"
    assert entry.defs == ["father"]


@pytest.mark.parametrize(
    "usage, expected",
    [
        (
            "chief, (fore-) father(-less), × patrimony, principal. Compare names in 'Abi-'.",
            ["chief", "father", "patrimony", "principal"],
        ),
        (
            "(all) along, apace, behave (self), + wilderness",
            ["along", "apace", "behave", "wilderness"],
        ),
        ("call (gather) together; give ear", ["call together", "give ear"]),
        ("give (perceive by the) ear, hear(-ken). See 239.", ["give ear", "hear"]),
        ("Aven. See also 204, 1007.", ["aven"]),
        ("behold, lo, see.", ["behold", "lo", "see"]),
        ("(that) see(-th).", ["see"]),
        ("mercy [as such unrepresented in English], (pure) gold", ["mercy", "gold"]),
        ("pure) gold, ) again, -th", ["pure gold", "again"]),
        ("Go, go, 40", ["go"]),
        ("", []),
    ],
)
def test_parse_usage_keeps_only_the_plain_renderings(usage, expected):
    assert parse_usage(usage) == expected


def test_index_glosses_groups_glosses_by_strong_id():
    index = {
        "aac": {"strong": "H1", "gloss": "father"},
        "aad": {"strong": "H1", "gloss": "ancestor"},
        "aae": {"strong": "H2", "gloss": "green"},
        "aaf": {"gloss": "no strong id"},
        "aag": {"strong": "H3"},
    }

    assert index_glosses(index) == {"H1": ["father", "ancestor"], "H2": ["green"]}


def test_lexical_element_takes_its_senses_from_the_entry_and_the_glosses():
    entry = StrongLexiconEntry(
        **{**ENTRY_JSON, "defs": ["father", "Ancestor"], "usage": "chief, × father"}
    )

    assert strong_to_lexical_element(entry, ["Father", "sire"]) == LexicalElement(
        definition="father",
        sense="chief, × father",
        pos="n-m",
        lang="heb",
        glosses=["father", "sire", "ancestor"],
        usages=["chief", "father"],
    )


def test_strong_elements_have_a_sense_each():
    assert len(STRONG_ELEMENTS) == len(STRONG_LEXICON.entries)
    assert all(element.glosses or element.usages for element in STRONG_ELEMENTS)


def test_strong_entries_without_a_meaning_get_glosses_from_the_index():
    assert STRONG_LEXICON.entries["H2"].meaning == ""
    assert "father" in STRONG_GLOSSES["H2"]
