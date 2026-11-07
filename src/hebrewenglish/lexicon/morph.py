from dataclasses import dataclass
from typing import Any, cast

from hebrewenglish.common.cite import Cite, cite_from_oshb
from hebrewenglish.common.strong import Strong, parse_strong
from hebrewenglish.lexicon.morphs import codes

from .morphs.codes import MorphCode


@dataclass
class VariantEntry:
    text: str
    count: int
    refs: list[Cite]


type TableEntry = list[VariantEntry]


type MorphTable = dict[MorphCode, TableEntry]


def process_variant(usages: dict) -> VariantEntry:
    text = usages.get("text", "")
    count = usages.get("count", 0)
    refs: list[Cite] = [cite_from_oshb(ref) for ref in usages.get("refs", [])]

    return VariantEntry(text=text, count=count, refs=refs)


def process_usage(key: str, value: dict) -> tuple[list[MorphCode], TableEntry]:

    language = codes.Language(key[0])
    parse_code = [codes.parse_code(key1, language) for key1 in key[1:].split("/")]
    if any(code is None for code in parse_code):
        raise TypeError(f"Invalid code: {key}")
    usages = value["forms"]
    variants = [process_variant(usage) for usage in usages]
    return cast(list[MorphCode], parse_code), variants


type Morphology = dict[Strong | str, MorphTable]


def process_morph_data(morph_data: dict) -> MorphTable:
    table = {}
    for key, value in morph_data.items():
        entry = process_usage(key, value)
        for code in entry[0]:
            table.setdefault(code, []).extend(entry[1])
    return table


class MorphData:
    _raw_data: Any
    _data: Morphology

    def __init__(self, morph):
        self._raw_data = morph
        self.startup()

    def startup(self):
        self._data = {}
        for key, value in self._raw_data.items():
            if isinstance(key, str):
                # Prefix lemmas such as "b" have no Strong number, so they stay as text
                self._data[parse_strong(key) or key] = process_morph_data(
                    value["usages"]
                )
            elif isinstance(key, int):
                self._data[Strong(key)] = process_morph_data(value["usages"])
            else:
                raise TypeError(f"Invalid key type: {key}")

    def __str__(self):
        return str(self._data)
