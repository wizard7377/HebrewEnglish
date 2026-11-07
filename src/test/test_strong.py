import pytest

from hebrewenglish.common.strong import Strong, parse_strong


def test_strong_numbers_compare_by_value():
    assert Strong(1) == Strong(1)
    assert Strong(122, "a") == Strong(122, "a")
    assert Strong(122, "a") != Strong(122, "b")
    assert Strong(122, "a") != Strong(122)


def test_strong_numbers_are_hashable():
    assert {Strong(122, "a"): 1}[Strong(122, "a")] == 1


def test_strong_numbers_are_not_ints():
    assert Strong(1) != 1


def test_parse_plain_number():
    assert parse_strong("430") == Strong(430)


def test_parse_number_with_modifier():
    assert parse_strong("122a") == Strong(122, "a")


@pytest.mark.parametrize("text", ["", "b", "a1", "12ab", "12 a", "H1"])
def test_parse_rejects_other_text(text: str):
    assert parse_strong(text) is None
