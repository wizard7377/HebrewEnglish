import unicodedata

import pytest

from hebrewenglish.backend.logic import FormRecord, LemmaMorphology
from hebrewenglish.common.books import format_oshb_ref
from hebrewenglish.common.strong import Strong
from hebrewenglish.gui.adapter import format_references, lemma_result, split_suffix
from hebrewenglish.gui.model import Attestation, SuffixId, resolve_form


def form(text, *refs):
    return [FormRecord(text, len(refs), list(refs))]


# A hand-built slice of šāmar: a plain perfect, an imperative attested with a suffix, and a construct infinitive
SHAMAR = LemmaMorphology(
    key="8104",
    lemma="שָׁמַר",
    xlit="šāmar",
    gloss="keep",
    pos="V",
    lang="heb",
    count=5,
    index=None,
    usages={
        "HVqp3ms": form("שָׁמַר", "Gen.37.11", "1Kgs.11.10"),
        "HVqp3cp": form("שָׁמְרוּ", "Deut.33.9"),
        "HVqv2ms": form("שְׁמֹר", "Deut.4.9"),
        "HVqv2ms/Sp1cs": form("שָׁמְרֵנִי", "Ps.16.1"),
        "HVNv2ms": form("הִשָּׁמֶר", "Gen.24.6"),
        "HVqc": form("שְׁמֹר", "Gen.3.24"),
    },
)


def group(result, stem, group_id):
    return next(g for g in result.groups_for(stem) if g.id == group_id)


def test_oshb_references_read_as_english_books():
    assert format_oshb_ref("Gen.2.24") == "Genesis 2:24"
    assert format_oshb_ref("1Sam.21.5") == "1 Samuel 21:5"


def test_references_are_ordered_deduplicated_and_capped():
    refs = ["Ps.1.1", "Gen.1.1", "Gen.1.1", *[f"Exod.{n}.1" for n in range(1, 8)]]
    assert format_references(refs) == (
        "Genesis 1:1",
        "Exodus 1:1",
        "Exodus 2:1",
        "Exodus 3:1",
        "Exodus 4:1",
        "Exodus 5:1",
        "+3 more",
    )


def test_suffix_splits_off_its_letters():
    assert split_suffix("שָׁמְרֵנִי", SuffixId.P1CS) == ("שָׁמְרֵ", "נִי")
    assert split_suffix("לוֹ", SuffixId.P3MS) == ("ל", "וֹ")
    # Nothing matches, so the whole form is the base
    assert split_suffix("לָכֶנָה", SuffixId.P2FP) == ("לָכֶנָה", "")


def test_verbs_group_by_stem_then_conjugation():
    result = lemma_result("H8104", None, SHAMAR, "שׁמר")
    assert result.part_of_speech == "Verb"
    assert result.stems == ["Qal", "Niphal"]
    assert [g.id for g in result.groups_for("Qal")] == ["perfect", "imperative", "infinitive"]
    assert [g.id for g in result.groups_for("Niphal")] == ["imperative"]
    perfect = group(result, "Qal", "perfect")
    assert [(row.label, row.form) for row in perfect.rows] == [
        ("3rd masc. singular", "שָׁמַר"),
        ("3rd common plural", "שָׁמְרוּ"),
    ]
    assert perfect.rows[0].references == ("Genesis 37:11", "1 Kings 11:10")
    assert [row.label for row in group(result, "Qal", "infinitive").rows] == ["Construct"]


def test_only_attested_suffixed_forms_are_shown():
    result = lemma_result("H8104", None, SHAMAR, "שׁמר")
    imperative = group(result, "Qal", "imperative").rows[0]
    suffixed = resolve_form(imperative, result, SuffixId.P1CS)
    assert suffixed.form == "שָׁמְרֵנִי"
    assert suffixed.attestation is Attestation.ATTESTED
    assert suffixed.references == ("Psalm 16:1",)
    assert resolve_form(imperative, result, SuffixId.P3MS) is None


@pytest.fixture(scope="module")
def backend():
    from hebrewenglish.backend.logic import Backend

    return Backend()


@pytest.fixture(scope="module")
def lookup(backend):
    from hebrewenglish.gui.adapter import make_lookup

    return make_lookup(backend)


def real_result(backend, strong, key=None):
    lemma = next(l for l in backend.get_morphology(strong) if key is None or l.key == key)
    return lemma_result(f"H{strong.index}", backend.get_lexicon_entry(strong), lemma, backend.root(lemma))


@pytest.mark.model
def test_guard_finds_shamar_with_its_qal_perfect(lookup):
    shamar = next(r for r in lookup("guard") if r.id == "H8104")
    assert shamar.part_of_speech == "Verb"
    assert shamar.stems[0] == "Qal"
    row = next(r for r in group(shamar, "Qal", "perfect").rows if r.label == "3rd masc. singular")
    # The WLC writes the shin dot before the vowel, which NFC reorders
    assert unicodedata.normalize("NFC", row.form) == unicodedata.normalize("NFC", "שָׁמַר")
    assert row.attestation is Attestation.ATTESTED
    assert any(ref.startswith("Genesis") for ref in row.references)


@pytest.mark.model
def test_derived_noun_borrows_its_root_and_takes_possessives(backend):
    mishmeret = real_result(backend, Strong(4931))
    assert mishmeret.root == "שׁמר"
    assert any(suffix is SuffixId.P3MS for _, suffix in mishmeret.suffixed_forms)


@pytest.mark.model
def test_preposition_contracts_with_suffixes():
    from hebrewenglish.backend.logic import lemma_morphology
    from hebrewenglish.lexicon.res import MORPH_DATA

    le = lemma_result("H0", None, lemma_morphology("l", MORPH_DATA["l"]), None)
    assert le.part_of_speech == "Preposition"
    base = next(row for row in le.morphology[0].rows if row.label == "Base form")
    assert unicodedata.normalize("NFC", resolve_form(base, le, SuffixId.P3MP).form) == "לָהֶם"


@pytest.mark.model
def test_entry_without_morphology_still_builds(backend):
    assert backend.get_morphology(Strong(25)) == []
    result = lemma_result("H25", backend.get_lexicon_entry(Strong(25)), None, None)
    assert result.morphology == []
    assert result.lemma
