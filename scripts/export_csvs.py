"""Exports two CSVs to exports/: every verse of the Torah in Hebrew with an English translation, and every
word form in the Hebrew Bible with its morphology.

Run with ``.venv/bin/python scripts/export_csvs.py``. The verses come from Sefaria (Hebrew: Miqra according to
the Masorah, CC BY-SA; English: JPS 1917, public domain); the word forms from the OSHB data in lexicon/res.
"""

import csv
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from hebrewenglish.common.books import format_oshb_ref, oshb_sort_key
from hebrewenglish.common.strong import parse_strong
from hebrewenglish.lexicon.morphs.codes import (
    Language,
    Person,
    SuffixMorphCode,
    VerbStemAramaic,
    VerbStemHebrew,
    parse_code,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "exports"
MORPH = ROOT / "src/hebrewenglish/lexicon/res/morph.json"

TORAH = {"Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34}
HEBREW_VERSION = "Miqra according to the Masorah"
ENGLISH_VERSION = "The Holy Scriptures: A New Translation (JPS 1917)"
# Excel only reads a CSV as UTF-8 when it starts with a byte-order mark
ENCODING = "utf-8-sig"

# Open and closed paragraph marks the Masoretic text sets between verses
_PARAGRAPH = re.compile(r"\s*\{[פס]\}\s*")
# Cantillation marks and meteg, leaving the vowel points
_ACCENTS = re.compile("[֑-ֽ֯]")


def _chapter(book: str, chapter: int) -> list[dict[str, str]]:
    versions = f"version=hebrew|{quote(HEBREW_VERSION)}&version=english|{quote(ENGLISH_VERSION)}"
    url = f"https://www.sefaria.org/api/v3/texts/{quote(f'{book} {chapter}')}?{versions}&return_format=text_only"
    with urlopen(url, timeout=60) as response:
        data = json.load(response)
    texts = {version["language"]: version["text"] for version in data["versions"]}
    hebrew, english = texts["he"], texts["en"]
    if len(hebrew) != len(english):
        raise ValueError(f"{book} {chapter}: {len(hebrew)} Hebrew verses but {len(english)} English")
    rows = []
    for verse, (he, en) in enumerate(zip(hebrew, english), 1):
        he = _PARAGRAPH.sub(" ", he).strip()
        rows.append(
            {
                "reference": f"{book} {chapter}:{verse}",
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "hebrew": he,
                "hebrew_without_cantillation": unicodedata.normalize("NFC", _ACCENTS.sub("", he)),
                "english": " ".join(en.split()),
            }
        )
    return rows


def export_torah_verses() -> int:
    chapters = [(book, chapter) for book, count in TORAH.items() for chapter in range(1, count + 1)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = [row for chapter in pool.map(lambda c: _chapter(*c), chapters) for row in chapter]
    with open(OUT / "torah_verses.csv", "w", newline="", encoding=ENCODING) as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _words(name: str) -> str:
    """ "SequentialImperfect" -> "sequential imperfect"."""
    return re.sub(r"(?<=[a-z])([A-Z])", lambda m: " " + m[1], name).lower()


def _value(part: object) -> str:
    if part is None:
        return ""
    # Stems are names, so they keep their capital: "Qal", "Hithpael", "Qal passive"
    if isinstance(part, VerbStemHebrew | VerbStemAramaic):
        return _words(part.name).capitalize()
    if isinstance(part, Person):
        return {Person.First: "1st", Person.Second: "2nd", Person.Third: "3rd"}[part]
    return _words(part.name)


def _suffix(code: SuffixMorphCode) -> str:
    parts = [_value(code.person), _value(code.gender), _value(code.number)]
    return " ".join([part for part in parts if part] + [_value(code.typ)])


def _morphology(usage: str) -> dict[str, str]:
    """The parts of a code such as "HVqp3ms/Sp3fs", spelled out."""
    language = Language(usage[0])
    own, *suffixes = (parse_code(segment, language) for segment in usage[1:].split("/"))
    info = {"language": _value(language)}
    if own is not None:
        info["part_of_speech"] = _words(type(own).__name__.removesuffix("MorphCode"))
        for field in fields(own):
            info["type" if field.name == "typ" else field.name] = _value(getattr(own, field.name))
    info["suffix"] = " + ".join(_suffix(code) for code in suffixes if isinstance(code, SuffixMorphCode))
    return info


WORD_COLUMNS = [
    "form",
    "consonants",
    "lemma",
    "transliteration",
    "gloss",
    "strong",
    "morph_code",
    "language",
    "part_of_speech",
    "type",
    "stem",
    "person",
    "gender",
    "number",
    "state",
    "suffix",
    "occurrences",
    "references",
]


# Excel holds at most 32,767 characters in a cell, which the commonest words (וְ, הַ, אֶת) would overrun
_MAX_REFERENCES_LENGTH = 32_000


def _references(refs: list[str]) -> str:
    shown: list[str] = []
    length = 0
    for ref in sorted(refs, key=oshb_sort_key):
        text = format_oshb_ref(ref)
        if length + len(text) + 2 > _MAX_REFERENCES_LENGTH:
            return "; ".join(shown) + f"; +{len(refs) - len(shown):,} more"
        shown.append(text)
        length += len(text) + 2
    return "; ".join(shown)


def _lemma_order(key: str) -> tuple[int, str]:
    # Numbered lemmas in Strong's order, then the prefixes (ו, ה, ב...) that have letters for keys
    strong = parse_strong(key)
    return (strong.index, strong.modifier or "") if strong else (10**6, key)


def export_word_forms() -> int:
    lemmas = json.loads(MORPH.read_text(encoding="utf-8"))["lemmas"]
    count = 0
    with open(OUT / "bible_word_forms.csv", "w", newline="", encoding=ENCODING) as file:
        writer = csv.DictWriter(file, fieldnames=WORD_COLUMNS, restval="")
        writer.writeheader()
        for key in sorted(lemmas, key=_lemma_order):
            record = lemmas[key]
            for usage, attested in record["usages"].items():
                morphology = _morphology(usage)
                for form in sorted(attested["forms"], key=lambda form: -form["count"]):
                    writer.writerow(
                        {
                            "form": unicodedata.normalize("NFC", form["text"]),
                            "consonants": form["consonantal"],
                            "lemma": unicodedata.normalize("NFC", record.get("lemma") or ""),
                            "transliteration": record.get("xlit", ""),
                            "gloss": record.get("gloss", ""),
                            "strong": record.get("strong", ""),
                            "morph_code": usage,
                            **morphology,
                            "occurrences": form["count"],
                            "references": _references(form["refs"]),
                        }
                    )
                    count += 1
    return count


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(f"{export_word_forms():,} word forms")
    print(f"{export_torah_verses():,} Torah verses")
