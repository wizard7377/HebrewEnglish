import numpy as np
import pytest
from model2vec import StaticModel

from hebrewenglish.lexicon.matcher import LexicalElement, Matcher

VECTORS = {
    "castle": [1.0, 0.0],
    "palace": [0.9, 0.2],
    "sword": [0.5, 0.5],
    "knot": [0.1, 0.9],
    "riddle": [0.0, 1.0],
    # These two have the same directions as castle and sword, at very different lengths.
    "tower": [0.1, 0.0],
    "mountain": [5.0, 5.0],
}


class FakeModel:
    """
    Stands in for StaticModel with fixed embeddings, so that these tests need no download.
    Like StaticModel, it returns a 1D array for a single string and only normalizes when asked to.
    """

    def __init__(self):
        self.encoded = []

    def encode(self, sentences, normalize=False):
        self.encoded.append(sentences)
        single = isinstance(sentences, str)
        vectors = np.array(
            [VECTORS[s] for s in ([sentences] if single else sentences)],
            dtype=np.float32,
        )
        if normalize:
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors[0] if single else vectors


def element(definition: str, pos: str = "n-m") -> LexicalElement:
    return LexicalElement(definition, f"sense of {definition}", pos)


def definitions(matches: list[tuple[int, LexicalElement]]) -> list[str]:
    return [match.definition for _, match in matches]


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def word_list() -> list[LexicalElement]:
    return [element(d) for d in ["riddle", "sword", "palace", "knot", "castle"]]


def test_orders_best_match_first(word_list, fake_model):
    matcher = Matcher(word_list, fake_model)

    assert definitions(matcher.get_matches("castle")) == [
        "castle",
        "palace",
        "sword",
        "knot",
    ]


def test_returns_the_elements_from_the_word_list(word_list, fake_model):
    matcher = Matcher(word_list, fake_model)

    [(index, match)] = matcher.get_matches("palace", 1)

    assert index == 2
    assert match is word_list[2]


def test_n_defaults_to_four(word_list, fake_model):
    assert len(Matcher(word_list, fake_model).get_matches("castle")) == 4


@pytest.mark.parametrize("n, expected", [(0, 0), (1, 1), (2, 2), (5, 5), (100, 5)])
def test_returns_at_most_n_elements(word_list, fake_model, n, expected):
    assert len(Matcher(word_list, fake_model).get_matches("castle", n)) == expected


def test_scores_by_direction_rather_than_length(fake_model):
    matcher = Matcher([element("mountain"), element("tower")], fake_model)

    assert definitions(matcher.get_matches("castle")) == ["tower", "mountain"]


def test_matches_against_the_definition_and_not_the_sense(fake_model):
    knot = LexicalElement("knot", "castle", "n-m")
    palace = LexicalElement("palace", "riddle", "n-m")
    matcher = Matcher([knot, palace], fake_model)

    assert matcher.get_matches("castle", 1) == [(1, palace)]


def test_encodes_the_word_list_only_once(word_list, fake_model):
    matcher = Matcher(word_list, fake_model)
    matcher.get_matches("castle")
    matcher.get_matches("sword")

    assert fake_model.encoded == [[e.definition for e in word_list], "castle", "sword"]


@pytest.mark.parametrize("pos", ["n-pr", "n-pr-m", "n-pr-loc", "n-pr-m n-pr-loc"])
def test_proper_nouns_rank_below_a_weaker_common_match(fake_model, pos):
    matcher = Matcher([element("castle", pos), element("sword")], fake_model)

    assert definitions(matcher.get_matches("castle")) == ["sword", "castle"]


@pytest.mark.parametrize(
    "pos", ["n-m", "v", "a", "", "n-m n-pr-m", "a n-pr-m", "n-pr-m n-m"]
)
def test_other_parts_of_speech_are_not_penalized(fake_model, pos):
    matcher = Matcher([element("castle", pos), element("sword")], fake_model)

    assert definitions(matcher.get_matches("castle")) == ["castle", "sword"]


def test_proper_noun_factor_sets_the_size_of_the_penalty(fake_model):
    word_list = [element("castle", "n-pr-loc"), element("palace"), element("sword")]
    matcher = Matcher(word_list, fake_model, proper_noun_factor=0.9)

    assert definitions(matcher.get_matches("castle")) == ["palace", "castle", "sword"]


def test_proper_noun_factor_of_one_changes_nothing(fake_model):
    word_list = [element("palace"), element("castle", "n-pr-loc")]
    matcher = Matcher(word_list, fake_model, proper_noun_factor=1.0)

    assert definitions(matcher.get_matches("castle")) == ["castle", "palace"]


def test_scores_by_the_best_sense_rather_than_a_blend_of_them(fake_model):
    many_senses = LexicalElement("many senses", "", "n-m", glosses=["riddle", "castle"])
    matcher = Matcher([element("palace"), many_senses], fake_model)

    assert matcher.get_matches("castle", 1) == [(1, many_senses)]


def test_encodes_senses_in_place_of_the_definition(fake_model):
    Matcher(
        [LexicalElement("knot", "", "n-m", glosses=["castle"], usages=["sword"])],
        fake_model,
    )

    assert fake_model.encoded == [["castle", "sword"]]


def test_usages_alone_replace_the_definition(fake_model):
    Matcher([LexicalElement("knot", "", "n-m", usages=["sword"])], fake_model)

    assert fake_model.encoded == [["sword"]]


def test_a_usage_counts_for_less_than_a_gloss(fake_model):
    usage = LexicalElement("usage", "", "n-m", usages=["castle"])
    matcher = Matcher([usage, element("palace")], fake_model, popularity_factor=0)

    assert definitions(matcher.get_matches("castle")) == ["palace", "usage"]


def test_usage_factor_of_one_changes_nothing(fake_model):
    usage = LexicalElement("usage", "", "n-m", usages=["castle"])
    matcher = Matcher(
        [element("palace"), usage], fake_model, usage_factor=1.0, popularity_factor=0
    )

    assert definitions(matcher.get_matches("castle")) == ["usage", "palace"]


def test_aramaic_loses_a_tie_to_hebrew(fake_model):
    aramaic = LexicalElement("castle", "aramaic", "n-m", lang="arc")
    hebrew = LexicalElement("castle", "hebrew", "n-m")
    matcher = Matcher([aramaic, hebrew], fake_model)

    assert matcher.get_matches("castle", 1) == [(1, hebrew)]


def test_aramaic_factor_sets_the_size_of_the_penalty(fake_model):
    word_list = [LexicalElement("castle", "", "n-m", lang="arc"), element("palace")]

    assert definitions(Matcher(word_list, fake_model).get_matches("castle")) == [
        "palace",
        "castle",
    ]
    assert definitions(
        Matcher(word_list, fake_model, aramaic_factor=1.0).get_matches("castle")
    ) == ["castle", "palace"]


def test_popularity_breaks_a_tie(fake_model):
    rare = LexicalElement("rare", "", "n-m", glosses=["castle"])
    common = LexicalElement(
        "common", "", "n-m", glosses=["castle"], usages=["knot", "riddle"]
    )
    matcher = Matcher([rare, common], fake_model)

    assert definitions(matcher.get_matches("castle")) == ["common", "rare"]


def test_popularity_factor_sets_the_size_of_the_boost(fake_model):
    common = LexicalElement(
        "common", "", "n-m", glosses=["palace"], usages=["knot", "riddle"]
    )
    word_list = [element("castle"), common]

    assert definitions(
        Matcher(word_list, fake_model, popularity_factor=0).get_matches("castle")
    ) == ["castle", "common"]
    assert definitions(
        Matcher(word_list, fake_model, popularity_factor=1.0).get_matches("castle")
    ) == ["common", "castle"]


@pytest.fixture(
    scope="module", params=[True, False], ids=["normalized", "unnormalized"]
)
def real_model(request) -> StaticModel:
    return StaticModel.from_pretrained(
        "minishlab/potion-base-8M", normalize=request.param, force_download=False
    )


@pytest.mark.model
@pytest.mark.parametrize(
    "word, expected",
    [
        ("castle", "palace"),
        ("dad", "father"),
        ("puzzle", "riddle"),
        ("weapon", "sword"),
        ("knot", "knot"),
    ],
)
def test_real_model_ranks_the_related_word_first(real_model, word, expected):
    word_list = [
        element(d) for d in ["palace", "father", "riddle", "knot", "sword", "crown"]
    ]

    assert definitions(Matcher(word_list, real_model).get_matches(word, 1)) == [
        expected
    ]


@pytest.mark.model
def test_real_model_ranks_an_element_without_text_last(real_model):
    word_list = [element(""), element("father"), element("sword")]

    assert definitions(Matcher(word_list, real_model).get_matches("dad")) == [
        "father",
        "sword",
        "",
    ]
