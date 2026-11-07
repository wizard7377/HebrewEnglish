import pytest

from hebrewenglish.lexicon.similar import HebrewIndex, IndexedLemma, consonants, skeleton

LEMMAS = [
    IndexedLemma("8104", "שָׁמַר", ("שָׁמַר", "יִשְׁמֹר", "שְׁמַרְתֶּם", "שֹׁמֵר"), "שמר", 469),
    IndexedLemma("8107", "שִׁמֻּר", (), "שמר", 2),
    IndexedLemma("4931", "מִשְׁמֶרֶת", ("מִשְׁמֶרֶת",), "שמר", 78),
    IndexedLemma("4428", "מֶלֶךְ", ("מֶלֶךְ", "מַלְכֵי"), "מלך", 2523),
    IndexedLemma("4427", "מָלַךְ", ("מָלַךְ", "יִמְלֹךְ"), "מלך", 350),
    IndexedLemma("4752", "מַר", ("מַר",), None, 38),
    IndexedLemma("7965", "שָׁלוֹם", ("שָׁלוֹם",), None, 237),
]


@pytest.fixture(scope="module")
def index() -> HebrewIndex:
    return HebrewIndex(LEMMAS)


def test_consonants_drop_points_and_write_final_letters_as_medial():
    assert consonants("מֶלֶךְ") == "מלכ"
    assert consonants("שָׁלוֹם") == consonants("שלום") == "שלומ"


def test_skeleton_lets_plene_and_defective_spellings_meet():
    assert skeleton(consonants("שׁוֹמֵר")) == skeleton(consonants("שֹׁמֵר"))
    # A first ו or י is a consonant, not a mater
    assert skeleton("ישב") == "ישב"


def test_lemmas_spelled_alike_come_first_by_frequency_then_the_rest_of_their_root(index):
    assert index.search("שמר")[:3] == ["8104", "8107", "4931"]


def test_an_inflected_form_finds_its_lemma(index):
    assert index.search("שְׁמַרְתֶּם")[0] == "8104"


def test_pointing_and_final_letters_do_not_matter(index):
    assert index.search("מלך")[:2] == index.search("מֶלֶךְ")[:2] == ["4428", "4427"]


def test_prefixes_come_off_when_the_word_as_typed_is_not_found(index):
    assert index.search("והמלך")[:2] == ["4428", "4427"]


def test_plene_spelling_finds_the_defective_form(index):
    assert index.search("שומר")[0] == "8104"


def test_near_spellings_make_up_the_number_after_the_word_and_its_root(index):
    found = index.search("שמר")
    assert "4752" in found
    assert found.index("4752") > found.index("8107")


def test_nothing_hebrew_finds_nothing(index):
    assert index.search("guard") == []
    assert index.search("") == []


def test_the_number_of_results_is_capped(index):
    assert len(index.search("שמר", n=2)) == 2


def test_a_prefix_read_as_the_article_beats_one_read_as_a_hiphil(index):
    hiphil = IndexedLemma("4427", "מָלַךְ", ("מָלַךְ", "הַמְלֵךְ"), "מלך", 350)
    index = HebrewIndex([lemma if lemma.key != "4427" else hiphil for lemma in LEMMAS])
    assert index.search("והמלך")[0] == "4428"
