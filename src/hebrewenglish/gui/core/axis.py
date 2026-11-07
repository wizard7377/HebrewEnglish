from dataclasses import dataclass

from hebrewenglish.common.maybe import Maybe


@dataclass
class Labelled[T]:
    value: T
    label: Maybe[str]


def basic[T](value: T, label: Maybe[str] = None) -> Labelled[T]:
    # Keep the label as text; building ui.label here would run at import time, outside any page
    return Labelled(value, label)


type Axis = Labelled[list[Labelled[str]]]

GENDER: Axis = Labelled(
    [
        basic("Masculine", "Masculine gender"),
        basic("Feminine", "Feminine gender"),
        basic("Common", "Common gender"),
    ],
    "Gender",
)

NUMBER: Axis = Labelled(
    [
        basic("Singular", "Singular number"),
        basic("Plural", "Plural number"),
        basic("Dual", "Dual number"),
    ],
    "Number",
)

PERSON: Axis = Labelled(
    [
        basic("First", "First person"),
        basic("Second", "Second person"),
        basic("Third", "Third person"),
    ],
    "Person",
)
