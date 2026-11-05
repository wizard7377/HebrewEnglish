from hebrewenglish.gui.demo import LEXICAL_RESULTS, lookup
from hebrewenglish.gui.model import (
    Attestation,
    SuffixId,
    bare_consonant,
    highlight_segments,
    paradigm_people,
    paradigm_row,
    resolve_form,
    split_clusters,
)

RESULTS = {result.id: result for result in LEXICAL_RESULTS}
SHAMAR = RESULTS["verb-shamar"]
MISHMERET = RESULTS["noun-mishmeret"]
LE = RESULTS["preposition-le"]


def group(result, group_id):
    return next(g for g in result.morphology if g.id == group_id)


def row(result, group_id, form):
    return next(r for r in group(result, group_id).rows if r.form == form)


def test_no_suffix_keeps_the_row():
    resolved = resolve_form(row(SHAMAR, "perfect", "שָׁמַר"), SHAMAR, SuffixId.NONE)
    assert resolved.form == "שָׁמַר"
    assert resolved.suffix == ""
    assert resolved.attestation is Attestation.ATTESTED
    assert resolved.references == ("Genesis 2:15", "1 Samuel 21:5")


def test_verb_suffix_is_reconstructed_when_unattested():
    resolved = resolve_form(row(SHAMAR, "perfect", "שָׁמַר"), SHAMAR, SuffixId.P3MS)
    assert resolved.form == "שָׁמַרהוּ"
    assert resolved.suffix == "הוּ"
    assert resolved.transliteration == "šāmar-hû"
    assert resolved.attestation is Attestation.UNATTESTED
    assert resolved.references == ()


def test_attested_suffixed_form_overrides_reconstruction():
    resolved = resolve_form(row(SHAMAR, "imperative", "שְׁמֹר"), SHAMAR, SuffixId.P1CS)
    assert resolved.form == "שָׁמְרֵנִי"
    assert resolved.attestation is Attestation.ATTESTED
    assert resolved.references == ("Psalm 16:1",)


def test_nouns_take_possessive_suffixes():
    resolved = resolve_form(row(MISHMERET, "absolute", "מִשְׁמָרוֹת"), MISHMERET, SuffixId.P3MS)
    assert resolved.suffix == "וֹ"


def test_preposition_contracts_with_suffix():
    resolved = resolve_form(row(LE, "pronominal-contraction", "לְ"), LE, SuffixId.P3MP)
    assert resolved.form == "לָהֶם"
    assert resolved.attestation is Attestation.ATTESTED


def test_clusters_keep_points_with_their_letter():
    assert split_clusters("שָׁמַר") == ["שָׁ", "מַ", "ר"]
    assert bare_consonant("שָׁ") == "ש"


def test_highlight_marks_root_inflection_and_suffix():
    resolved = resolve_form(row(SHAMAR, "imperfect", "יִשְׁמֹר"), SHAMAR, SuffixId.P3MS)
    kinds = [kind for kind, _ in highlight_segments(resolved, SHAMAR.root)]
    assert kinds == ["inflection", "root", "root", "root", "suffix"]


def test_common_plural_fills_both_plural_columns():
    perfect = group(SHAMAR, "perfect")
    assert paradigm_row(perfect, "3rd", "mp") == paradigm_row(perfect, "3rd", "fp")
    assert paradigm_row(perfect, "3rd", "mp").form == "שָׁמְרוּ"


def test_imperative_and_participle_rows_fill_their_paradigms():
    imperative = group(SHAMAR, "imperative")
    participle = group(SHAMAR, "participle")
    assert paradigm_people(imperative) == ["2nd"]
    assert paradigm_row(imperative, "2nd", "ms").form == "שְׁמֹר"
    assert paradigm_row(participle, "Participle", "fp").form == "שֹׁמְרוֹת"


def test_nouns_hide_the_fixed_suffix_tab():
    assert [g.id for g in MISHMERET.visible_groups] == ["absolute", "construct"]


def test_lookup_only_knows_demo_queries():
    assert lookup(" Guard ") == LEXICAL_RESULTS
    assert lookup("xyz") == []


def test_suffixes_are_left_out_when_reconstruction_is_off():
    from dataclasses import replace

    attested_only = replace(SHAMAR, reconstruct_suffixes=False)
    assert resolve_form(row(SHAMAR, "perfect", "שָׁמַר"), attested_only, SuffixId.P3MS) is None
    assert resolve_form(row(SHAMAR, "imperative", "שְׁמֹר"), attested_only, SuffixId.P1CS).form == "שָׁמְרֵנִי"


def test_entries_without_stems_show_every_group():
    assert SHAMAR.stems == []
    assert SHAMAR.groups_for(None) == SHAMAR.visible_groups
