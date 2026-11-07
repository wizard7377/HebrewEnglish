import json
import pathlib
import re
from dataclasses import dataclass

from model2vec import StaticModel

from hebrewenglish.lexicon.matcher import LexicalElement, Matcher
from hebrewenglish.lexicon.morph import MorphData

CWD = pathlib.Path(__file__).resolve().parent


def get_resource_path(resource_path) -> pathlib.Path:
    return CWD / "res" / resource_path


def load_json_resource(resource_path):
    with open(get_resource_path(resource_path), "r") as f:
        return json.load(f)


AUG: dict = load_json_resource("aug.json")
BDB: dict = load_json_resource("bdb.json")
INDEX: dict = load_json_resource("index.json")
STRONG: dict = load_json_resource("strong.json")
MORPH: dict = load_json_resource("morph.json")
MORPH_DATA = MORPH["lemmas"]


@dataclass
class StrongLexiconEntry:
    id: str
    lemma: str
    xlit: str
    pron: str
    pos: str
    lang: str
    source: str
    meaning: str
    defs: list[str]
    usage: str
    see: list[str]


def json_to_strong_lexicon_entry(entry_json: dict) -> StrongLexiconEntry:

    return StrongLexiconEntry(
        id=entry_json.get("id", ""),
        lemma=entry_json.get("lemma", ""),
        xlit=entry_json.get("xlit", ""),
        pron=entry_json.get("pron", ""),
        pos=entry_json.get("pos", ""),
        lang=entry_json.get("lang", ""),
        source=entry_json.get("source", ""),
        meaning=entry_json.get("meaning", ""),
        defs=entry_json.get("defs", []),
        usage=entry_json.get("usage", ""),
        see=entry_json.get("see", []),
    )


@dataclass
class StrongLexicon:
    entries: dict[str, StrongLexiconEntry]


def json_to_strong_lexicon(entries_json: dict) -> StrongLexicon:
    return StrongLexicon(
        entries={
            entry_id: json_to_strong_lexicon_entry(entry_json)
            for entry_id, entry_json in entries_json.items()
        }
    )


STRONG_LEXICON: StrongLexicon = json_to_strong_lexicon(STRONG)


def parse_usage(usage: str) -> list[str]:
    """
    Splits a Strong's usage note, such as "chief, (fore-) father(-less), × patrimony", into its plain renderings.
    """
    # Cross references are capitalized or lead to a number, as the renderings "see" and "compare" do not.
    usage = re.sub(
        r"\b(?:See|Compare)\b.*$|\b(?:see|compare)\b(?: also)? \d.*$", " ", usage
    )
    # Brackets are not always balanced, so the last alternative catches the ones that are left over.
    usage = re.sub(r"\([^)]*\)|\[[^\]]*\]|\b\d+\b|[×+()\[\]]", " ", usage)
    renderings = [
        " ".join(part.split()).strip("' ").lower() for part in re.split(r"[,;.]", usage)
    ]
    return list(dict.fromkeys(r for r in renderings if len(r) > 1 and r[0].isalpha()))


def index_glosses(index: dict) -> dict[str, list[str]]:
    glosses: dict[str, list[str]] = {}
    for entry in index.values():
        if "strong" in entry and "gloss" in entry:
            glosses.setdefault(entry["strong"], []).append(entry["gloss"])
    return glosses


def strong_to_lexical_element(
    entry: StrongLexiconEntry, glosses: list[str]
) -> LexicalElement:
    return LexicalElement(
        definition=entry.meaning,
        sense=entry.usage,
        pos=entry.pos,
        lang=entry.lang,
        glosses=list(dict.fromkeys(gloss.lower() for gloss in glosses + entry.defs)),
        usages=parse_usage(entry.usage),
    )


STRONG_GLOSSES: dict[str, list[str]] = index_glosses(INDEX)

STRONG_ELEMENTS: list[LexicalElement] = [
    strong_to_lexical_element(entry, STRONG_GLOSSES.get(entry.id, []))
    for entry in STRONG_LEXICON.entries.values()
]
STRONG_MATCHER: Matcher = Matcher(
    word_list=STRONG_ELEMENTS,
    model=StaticModel.from_pretrained("minishlab/potion-base-32M"),
)

MORPHOLOGY = MorphData(MORPH_DATA)
