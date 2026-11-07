from hebrewenglish.lexicon import sefaria
from hebrewenglish.lexicon.sefaria import Sense, find_entry, lookup

# Trimmed from https://www.sefaria.org/api/words/שמר
SHAMAR = [
    {
        "headword": "שׁוֹמֵר",
        "parent_lexicon": "BDB Augmented Strong",
        "strong_number": "7763",
        "content": {"senses": [{"definition": "Shomer"}]},
    },
    {
        "headword": "שָׁמַר",
        "parent_lexicon": "BDB Augmented Strong",
        "strong_number": "8104",
        "content": {
            "morphology": "v",
            "senses": [
                {
                    "definition": "to keep,  guard,  observe, give heed",
                    "senses": [
                        {
                            "senses": [
                                {"definition": "to keep,  have charge of"},
                                {
                                    "definition": "to keep,  guard",
                                    "senses": [{"definition": "watch,  watchman (participle)"}],
                                },
                            ],
                            "grammar": {"verbal_stem": "Qal"},
                        },
                        {"definition": " to keep, pay heed", "grammar": {"verbal_stem": "Piel"}},
                    ],
                }
            ],
        },
    },
    {
        "headword": "שָׁמַר",
        "parent_lexicon": "BDB Dictionary",
        "strong_numbers": ["8104"],
        "content": {"senses": [{"definition": "<strong>vb. keep</strong>"}]},
    },
]


def test_senses_split_by_stem():
    entry = find_entry(SHAMAR, "8104")
    assert entry is not None and entry.headword == "שָׁמַר"
    assert entry.senses == (Sense("to keep, guard, observe, give heed"),)
    assert entry.stems == {
        "Qal": (
            Sense("to keep, have charge of"),
            Sense("to keep, guard", (Sense("watch, watchman (participle)"),)),
        ),
        "Piel": (Sense("to keep, pay heed"),),
    }


def test_entry_is_chosen_by_strong_number_and_lexicon():
    assert find_entry(SHAMAR, "7763") == sefaria.SefariaLexicon("שׁוֹמֵר", (Sense("Shomer"),))
    assert find_entry(SHAMAR, "1234") is None


def test_aramaic_stem_names_follow_the_oshb():
    raw = [{"strong_number": "1124", "parent_lexicon": "BDB Augmented Strong", "content": {"senses": [
        {"definition": "to build", "grammar": {"verbal_stem": "P'al"}}
    ]}}]
    entry = find_entry(raw, "1124")
    assert entry is not None and set(entry.stems) == {"Peal"}


def test_lookup_asks_for_the_bare_consonants(monkeypatch):
    asked: list[str] = []

    def words(consonants: str) -> list:
        asked.append(consonants)
        return SHAMAR

    monkeypatch.setattr(sefaria, "_words", words)
    entry = lookup("שָׁמַר", "8104")
    assert asked == ["שמר"] and entry is not None and "Qal" in entry.stems


def test_lookup_falls_back_to_the_word_as_written_in_its_verse(monkeypatch):
    mibneh = [{"parent_lexicon": "BDB Augmented Strong", "strong_number": "4011", "headword": "מִבְנֶה",
               "content": {"senses": [{"definition": "structure"}]}}]
    monkeypatch.setattr(sefaria, "_words", lambda consonants: mibneh if consonants == "כמבנה" else [])
    monkeypatch.setattr(sefaria, "_verse_words", lambda ref: ("ועליו", "כמבנה", "עיר"))
    entry = lookup("מִבְנֶה", "4011", (("מִבְנֵה", "Ezekiel 40:2"),))
    assert entry is not None and entry.senses == (Sense("structure"),)
