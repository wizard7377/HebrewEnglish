"""Reconstruct the forms a verb lacks: fit its lexical choices to the forms it has, then fill each empty cell."""

from collections.abc import Collection, Iterator, Mapping
from dataclasses import dataclass, replace
from itertools import product

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.lexicon.morphs.codes import (
    Gender,
    Number,
    Person,
    State,
    VerbMorphCode,
    VerbStemHebrew,
    VerbTypes,
)

from .letters import comparable
from .paradigm import CELLS, TYPES, generate
from .render import Params
from .roots import VerbRoot, Weakness

SUPPORTED_STEMS = frozenset(TYPES)


@dataclass(frozen=True)
class Slot:
    """One cell of a verb's paradigm, by OSHB letters: stem, verb type, and person-gender-number."""

    stem: str
    typ: str
    cell: str


def slot_of(code: VerbMorphCode) -> Maybe[Slot]:
    """The paradigm cell a parsed OSHB code fills, or None for codes the paradigm has no cell for."""
    if (
        not isinstance(code.stem, VerbStemHebrew)
        or code.typ is None
        or code.stem.value not in SUPPORTED_STEMS
    ):
        return None
    typ = code.typ.value
    if code.stem is VerbStemHebrew.Niphal and code.typ is VerbTypes.PassiveParticiple:
        # The Niphal has one participle, which the OSHB sometimes tags passive
        typ = VerbTypes.ActiveParticiple.value
    if code.typ in (VerbTypes.InfinitiveAbsolute, VerbTypes.InfinitiveConstruct):
        return Slot(code.stem.value, typ, "")
    if code.gender is None or code.number is None:
        return None
    gender = "c" if code.gender in (Gender.Common, Gender.Both) else code.gender.value
    number = "s" if code.number is Number.Singular else "p"
    if code.typ in (VerbTypes.ActiveParticiple, VerbTypes.PassiveParticiple):
        # Construct participles (šōmərê) are a different form from the absolute the paradigm shows
        if code.state is State.Construct or gender == "c":
            return None
        return Slot(code.stem.value, typ, gender + number)
    if code.person is None:
        return None
    cell = f"{code.person.value}{gender}{number}"
    return Slot(code.stem.value, typ, cell) if cell in CELLS.get(typ, []) else None


def code_of(slot: Slot) -> VerbMorphCode:
    typ = VerbTypes(slot.typ)
    person = gender = number = state = None
    if len(slot.cell) == 3:
        person = Person(slot.cell[0])
    if slot.cell:
        gender, number = Gender(slot.cell[-2]), Number(slot.cell[-1])
    if typ in (VerbTypes.ActiveParticiple, VerbTypes.PassiveParticiple):
        state = State.Absolute
    return VerbMorphCode(VerbStemHebrew(slot.stem), typ, person, gender, number, state)


def slots(stem: str) -> Iterator[Slot]:
    """Every standard cell of a stem's paradigm."""
    for typ in TYPES.get(stem, []):
        for cell in CELLS[typ]:
            yield Slot(stem, typ, cell)


def default_params(root: VerbRoot) -> Params:
    """GKC's defaults: an a-imperfect beside a guttural and in stative verbs, ē in I-waw verbs, o otherwise."""
    weak = root.weaknesses
    if (
        weak & {Weakness.II_GUTTURAL, Weakness.III_GUTTURAL, Weakness.III_ALEPH}
        or root.perfect_theme != "a"
    ):
        theme = "a"
    elif Weakness.I_YOD in weak or "q" in root.irregular.first_like_waw:
        theme = "ē"
    else:
        theme = "o"
    return Params(imperfect_theme=theme, guttural_closes=root.irregular.guttural_closes)


def _choices(root: VerbRoot, stem: str) -> dict[str, list[object]]:
    """The parameters worth fitting for this root in this stem, each with its possible values."""
    weak = root.weaknesses
    choices: dict[str, list[object]] = {}
    if stem == "q" and not weak & {Weakness.III_HE, Weakness.HOLLOW, Weakness.GEMINATE}:
        choices["imperfect_theme"] = ["o", "a", "ē"]
    if Weakness.I_YOD in weak and stem in "qh":
        choices["waw_original"] = [True, False]
    if Weakness.I_GUTTURAL in weak and root.bare[0] in "הח" and stem in "qNhH":
        choices["guttural_closes"] = [False, True]
    return choices


def _matches(
    root: VerbRoot, params: Params, attested: Mapping[Slot, frozenset[str]]
) -> int:
    score = 0
    for slot, forms in attested.items():
        generated = generate(root, slot.stem, slot.typ, slot.cell, params)
        if generated is not None and comparable(generated) in forms:
            score += 1
    return score


def fit(root: VerbRoot, stem: str, attested: Mapping[Slot, Collection[str]]) -> Params:
    """The parameters that reproduce the most of the stem's attested forms; the defaults win ties."""
    default = default_params(root)
    known = {
        slot: frozenset(comparable(f) for f in forms)
        for slot, forms in attested.items()
        if slot.stem == stem
    }
    choices = _choices(root, stem)
    if not known or not choices:
        return default
    best, best_score = default, _matches(root, default, known)
    names = list(choices)
    for values in product(*choices.values()):
        candidate = replace(default, **dict(zip(names, values)))
        score = _matches(root, candidate, known)
        if score > best_score:
            best, best_score = candidate, score
    return best


def reconstruct(
    root: VerbRoot, stem: str, attested: Mapping[Slot, Collection[str]]
) -> dict[Slot, str]:
    """Generated forms for every cell of the stem with no attested form, after fitting to those it has."""
    params = fit(root, stem, attested)
    result: dict[Slot, str] = {}
    for slot in slots(stem):
        if slot in attested:
            continue
        form = generate(root, stem, slot.typ, slot.cell, params)
        if form is not None:
            result[slot] = form
    return result
