import json
import pathlib

import pytest

from hebrewenglish.common.strong import Strong
from hebrewenglish.lexicon import morph
from hebrewenglish.lexicon.morph import MorphData, Morphology, process_morph_data
from hebrewenglish.lexicon.morphs.codes import (
    ConjunctionMorphCode,
    Gender,
    Language,
    NounMorphCode,
    NounTypes,
    Number,
    Person,
    PrepositionMorphCode,
    State,
    SuffixMorphCode,
    SuffixTypes,
    parse_code,
)

# Read directly, as importing lexicon.res would load the embedding model too
MORPH_PATH = pathlib.Path(morph.__file__).parent / "res" / "morph.json"


@pytest.fixture(scope="module")
def lemmas() -> dict:
    with open(MORPH_PATH, encoding="utf-8") as f:
        return json.load(f)["lemmas"]


@pytest.fixture(scope="module")
def morphology(lemmas: dict) -> Morphology:
    return MorphData(lemmas)._data


def forms(text: str) -> dict:
    return {"count": 1, "forms": [{"text": text, "count": 1, "refs": []}]}


def texts(entry: morph.TableEntry) -> list[str]:
    return [variant.text for variant in entry]


def test_every_code_parses(lemmas: dict):
    keys = {key for entry in lemmas.values() for key in entry["usages"]}
    for key in keys:
        language = Language(key[0])
        for part in key[1:].split("/"):
            parsed = parse_code(part, language)
            assert parsed is not None, key
            assert parsed.write() == part


def test_every_lemma_loads(lemmas: dict, morphology: Morphology):
    assert len(lemmas) == 9271
    assert len(morphology) == len(lemmas)


def test_no_table_is_empty(morphology: Morphology):
    for lemma, table in morphology.items():
        assert table, lemma
        for code, entry in table.items():
            assert entry, (lemma, code)


def test_numbered_keys_are_strong_numbers(morphology: Morphology):
    assert all(not (isinstance(key, str) and key[0].isdigit()) for key in morphology)
    assert Strong(1) in morphology
    assert Strong(10) in morphology
    assert Strong(122, "a") in morphology
    assert Strong(122, "b") in morphology
    assert Strong(122) not in morphology


def test_prefix_keys_stay_text(morphology: Morphology):
    prefixes = [key for key in morphology if isinstance(key, str)]
    assert sorted(prefixes) == ["b", "c", "d", "i", "k", "l", "m", "s"]


def test_int_keys_become_strong_numbers():
    assert MorphData({1: {"usages": {}}})._data == {Strong(1): {}}


def test_invalid_key_type_is_rejected():
    with pytest.raises(ValueError):
        MorphData({1.5: {"usages": {}}})


def test_forms_are_read(morphology: Morphology):
    father = NounMorphCode(
        NounTypes.Common, Gender.Masculine, Number.Singular, State.Absolute
    )
    entry = morphology[Strong(1)][father]
    assert "אָב" in texts(entry)
    assert all(variant.count == len(variant.refs) for variant in entry)


def test_compound_codes_do_not_share_entries():
    table = process_morph_data(
        {
            "HR/Sp3ms": forms("a"),
            "HR": forms("b"),
            "HC/Sp3ms": forms("c"),
        }
    )
    suffix = SuffixMorphCode(
        SuffixTypes.Pronominal, Person.Third, Gender.Masculine, Number.Singular
    )
    assert texts(table[PrepositionMorphCode(None)]) == ["a", "b"]
    assert texts(table[suffix]) == ["a", "c"]
    assert texts(table[ConjunctionMorphCode()]) == ["c"]


def test_invalid_code_is_rejected():
    with pytest.raises(ValueError):
        process_morph_data({"HZ": forms("a")})


def test_missing_forms_fails_loudly():
    with pytest.raises(KeyError):
        process_morph_data({"HR": {"count": 1}})
