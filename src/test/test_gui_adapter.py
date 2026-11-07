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
    perfect = group(result, "Qal", "perfect")
    assert [
        (row.label, row.form)
        for row in perfect.rows
        if row.attestation is Attestation.ATTESTED
    ] == [
        ("3rd masc. singular", "שָׁמַר"),
        ("3rd common plural", "שָׁמְרוּ"),
    ]
    assert perfect.rows[0].references == ("Genesis 37:11", "1 Kings 11:10")
    infinitive = group(result, "Qal", "infinitive")
    assert [
        row.label for row in infinitive.rows if row.attestation is Attestation.ATTESTED
    ] == ["Construct"]


def test_gaps_in_attested_stems_are_reconstructed():
    result = lemma_result("H8104", None, SHAMAR, "שׁמר")
    assert (
        next(p.value for p in result.properties if p.label == "Verb class") == "Strong"
    )
    perfect = {row.label: row for row in group(result, "Qal", "perfect").rows}
    second_fp = perfect["2nd fem. plural"]
    assert second_fp.form == unicodedata.normalize("NFC", "שְׁמַרְתֶּן")
    assert second_fp.attestation is Attestation.UNATTESTED
    assert second_fp.note == "Reconstructed"
    assert perfect["3rd masc. singular"].attestation is Attestation.ATTESTED
    # Stems stay those the Bible attests, though each gains the conjugations it lacks
    assert result.stems == ["Qal", "Niphal"]
    assert "perfect" in [g.id for g in result.groups_for("Niphal")]
    # Reconstructed forms take no suffixes
    assert resolve_form(perfect["2nd fem. plural"], result, SuffixId.P1CS) is None


def test_sequential_forms_get_back_the_waw_the_oshb_writes_apart():
    result = lemma_result("H8104", None, SHAMAR, "שׁמר")
    rows = [
        row
        for group_id in ("sequential-perfect", "sequential-imperfect")
        for row in group(result, "Qal", group_id).rows
        if row.form
    ]
    assert rows and all(row.form.startswith("ו") for row in rows)
    assert all(not row.form.startswith("ו") for row in group(result, "Qal", "perfect").rows if row.form)


def test_reconstructed_base_of_a_suffix_only_slot_keeps_its_suffixed_forms():
    usages = {
        "HVqp3ms": form("שָׁמַר", "Gen.37.11"),
        "HVqv2fs/Sp1cs": form("שִׁמְרִינִי", "Ps.0.1"),
    }
    lemma = LemmaMorphology("8104", "שָׁמַר", "šāmar", "keep", "V", "heb", 2, None, usages)
    result = lemma_result("H8104", None, lemma, "שׁמר")
    row = next(
        r
        for r in group(result, "Qal", "imperative").rows
        if r.label == "2nd fem. singular"
    )
    assert row.form == unicodedata.normalize("NFC", "שִׁמְרִי")
    assert row.note == "Reconstructed · attested with suffixes"
    assert resolve_form(row, result, SuffixId.P1CS).attestation is Attestation.ATTESTED


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
    lemma = next(
        l for l in backend.get_morphology(strong) if key is None or l.key == key
    )
    return lemma_result(
        f"H{strong.index}",
        backend.get_lexicon_entry(strong),
        lemma,
        backend.root(lemma),
    )


@pytest.mark.model
def test_guard_finds_shamar_with_its_qal_perfect(lookup):
    shamar = next(r for r in lookup("guard") if r.id == "H8104")
    assert shamar.part_of_speech == "Verb"
    assert shamar.stems[0] == "Qal"
    assert shamar.occurrences is not None and shamar.occurrences > 400
    row = next(
        r
        for r in group(shamar, "Qal", "perfect").rows
        if r.label == "3rd masc. singular"
    )
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
    assert (
        unicodedata.normalize("NFC", resolve_form(base, le, SuffixId.P3MP).form)
        == "לָהֶם"
    )


@pytest.mark.model
def test_entry_without_morphology_still_builds(backend):
    assert backend.get_morphology(Strong(25)) == []
    result = lemma_result("H25", backend.get_lexicon_entry(Strong(25)), None, None)
    assert result.morphology == []
    assert result.lemma


@pytest.mark.model
def test_a_hebrew_word_finds_its_lemma_and_root_relatives(backend):
    from hebrewenglish.gui.adapter import make_hebrew_lookup

    lookup = make_hebrew_lookup(backend)
    found = [result.id for result in lookup("וַיִּשְׁמְרוּ")]
    assert found[0] == "H8104"
    assert "H4931" in found
    assert [result.id for result in lookup("והמלך")][:2] == ["H4428", "H4427a"]
    assert lookup("guard") == []
