"""Builds the page's view model from the backend: Strong's entries, OSHB forms and lexical-index roots."""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import lru_cache

from hebrewenglish.backend.logic import Backend, FormRecord, LemmaMorphology
from hebrewenglish.common.books import format_oshb_ref, oshb_sort_key
from hebrewenglish.common.maybe import Maybe
from hebrewenglish.common.strong import Strong
from hebrewenglish.gui.model import (
    SUFFIX_OPTIONS,
    Attestation,
    Category,
    LexicalResult,
    MorphologyGroup,
    MorphologyRow,
    Property,
    ResolvedForm,
    SuffixId,
    bare_consonant,
    split_clusters,
)
from hebrewenglish.inflect.generate import (
    SUPPORTED_STEMS,
    Slot,
    code_of,
    reconstruct,
    slot_of,
)
from hebrewenglish.inflect.letters import with_conjunction
from hebrewenglish.inflect.roots import VerbRoot, verb_root
from hebrewenglish.lexicon.morphs.codes import (
    AdjectiveMorphCode,
    Gender,
    Language,
    MorphCode,
    NounMorphCode,
    Number,
    PartOfSpeech,
    Person,
    PrepositionMorphCode,
    PrepositionTypes,
    PronounMorphCode,
    State,
    SuffixMorphCode,
    SuffixTypes,
    VerbMorphCode,
    VerbStemHebrew,
    VerbTypes,
    parse_code,
)
from hebrewenglish.lexicon.res import StrongLexiconEntry

MAX_REFERENCES = 6

# Group id, label, description and the verb types it collects, in display order
_CONJUGATIONS: list[tuple[str, str, str, tuple[VerbTypes, ...]]] = [
    (
        "perfect",
        "Perfect",
        "Completed action, commonly narrated as a whole.",
        (VerbTypes.SimplePerfect,),
    ),
    (
        "sequential-perfect",
        "Sequential perfect",
        "Perfect with waw-consecutive, carrying on future or instructional sequences.",
        (VerbTypes.SequentialPerfect,),
    ),
    (
        "imperfect",
        "Imperfect",
        "Incomplete, habitual, or future action.",
        (VerbTypes.Imperfect,),
    ),
    (
        "sequential-imperfect",
        "Sequential imperfect",
        "Imperfect with waw-consecutive, the main tense of past narrative.",
        (VerbTypes.SequentialImperfect,),
    ),
    (
        "cohortative",
        "Cohortative",
        "First-person resolve or wish: let me, let us.",
        (VerbTypes.Cohortative,),
    ),
    (
        "jussive",
        "Jussive",
        "Third- or second-person wish or command: may he, let him.",
        (VerbTypes.Jussive,),
    ),
    (
        "imperative",
        "Imperative",
        "Direct second-person command.",
        (VerbTypes.Imperative,),
    ),
    (
        "active-participle",
        "Active participle",
        "Ongoing action, or the one who performs it.",
        (VerbTypes.ActiveParticiple,),
    ),
    (
        "passive-participle",
        "Passive participle",
        "The one acted upon.",
        (VerbTypes.PassiveParticiple,),
    ),
    (
        "infinitive",
        "Infinitive",
        "Verbal noun: the absolute for emphasis, the construct after prepositions.",
        (VerbTypes.InfinitiveAbsolute, VerbTypes.InfinitiveConstruct),
    ),
]
_CONJUGATION_OF = {
    typ: index for index, (*_, types) in enumerate(_CONJUGATIONS) for typ in types
}

_STATES: dict[Maybe[State], tuple[str, str, str]] = {
    State.Absolute: ("absolute", "Absolute", "Free-standing form."),
    State.Construct: (
        "construct",
        "Construct",
        "Bound form, joined to a following noun or suffix.",
    ),
    State.Determined: (
        "determined",
        "Determined",
        "Aramaic emphatic state, marking the noun as definite.",
    ),
    None: ("forms", "Forms", "Attested forms."),
}

_PERSONS = {Person.Third: "3rd", Person.Second: "2nd", Person.First: "1st"}
_GENDER_ABBREVIATIONS = {
    Gender.Masculine: "masc.",
    Gender.Feminine: "fem.",
    Gender.Common: "common",
    Gender.Both: "common",
}
_GENDERS = {
    Gender.Masculine: "Masculine",
    Gender.Feminine: "Feminine",
    Gender.Common: "Common",
    Gender.Both: "Common",
}
# The paradigm has singular and plural columns only, so duals sit with the plurals
_NUMBERS = {Number.Singular: "singular", Number.Plural: "plural", Number.Dual: "plural"}
_NOUN_NUMBERS = {
    Number.Singular: "singular",
    Number.Plural: "plural",
    Number.Dual: "dual",
}
_ORDER = {
    **{p: i for i, p in enumerate([Person.Third, Person.Second, Person.First])},
    **{
        g: i
        for i, g in enumerate(
            [Gender.Masculine, Gender.Feminine, Gender.Common, Gender.Both]
        )
    },
    **{n: i for i, n in enumerate([Number.Singular, Number.Dual, Number.Plural])},
}


def _order(*parts: object) -> tuple[int, ...]:
    return tuple(_ORDER.get(part, len(_ORDER)) for part in parts)


def _words(name: str) -> str:
    """ "QalPassive" -> "Qal passive"."""
    return re.sub(r"(?<=[a-z])([A-Z])", lambda m: " " + m[1].lower(), name)


@dataclass(frozen=True)
class _Slot:
    """Where one code's forms go: a group, a row in it, and a rank so a better source can win the row."""

    group: str
    stem: Maybe[str]
    label: str
    order: tuple[int, ...]
    rank: int = 0


def _verb_slot(code: VerbMorphCode) -> Maybe[_Slot]:
    if code.typ is None or code.typ not in _CONJUGATION_OF:
        return None
    index = _CONJUGATION_OF[code.typ]
    group = _CONJUGATIONS[index][0]
    stem = _words(code.stem.name) if code.stem else None
    if code.typ in (VerbTypes.InfinitiveAbsolute, VerbTypes.InfinitiveConstruct):
        label = "Absolute" if code.typ is VerbTypes.InfinitiveAbsolute else "Construct"
        return _Slot(group, stem, label, (0 if label == "Absolute" else 1,))
    if code.gender is None or code.number is None:
        return None
    if code.typ in (VerbTypes.ActiveParticiple, VerbTypes.PassiveParticiple):
        # The paradigm has one cell per gender and number, so the construct only fills in for a missing absolute
        label = f"{_GENDERS[code.gender]} {_NUMBERS[code.number]}"
        return _Slot(
            group,
            stem,
            label,
            _order(code.number, code.gender),
            0 if code.state is not State.Construct else 1,
        )
    if code.person is None:
        return None
    label = f"{_PERSONS[code.person]} {_GENDER_ABBREVIATIONS[code.gender]} {_NUMBERS[code.number]}"
    return _Slot(group, stem, label, _order(code.person, code.number, code.gender))


def _nominal_slot(code: NounMorphCode | AdjectiveMorphCode) -> _Slot:
    group = _STATES.get(code.state, _STATES[None])[0]
    parts = [_GENDERS[code.gender]] if code.gender else []
    parts.append(_NOUN_NUMBERS[code.number] if code.number else "form")
    label = " ".join(parts)
    return _Slot(
        group, None, label[0].upper() + label[1:], _order(code.number, code.gender)
    )


def _other_slot(code: MorphCode, group: str) -> _Slot:
    match code:
        case PrepositionMorphCode(typ=PrepositionTypes.DefiniteArticle):
            return _Slot(group, None, "With article", (1,))
        case PronounMorphCode(person=person, gender=gender, number=number) if (
            number is not None
        ):
            parts = [_PERSONS[person]] if person else []
            parts += [_GENDER_ABBREVIATIONS[gender]] if gender else []
            parts.append(_NUMBERS[number])
            return _Slot(group, None, " ".join(parts), _order(person, number, gender))
        case _:
            return _Slot(group, None, "Base form", (0,))


def _slot(code: MorphCode, part_of_speech: str) -> Maybe[_Slot]:
    # A stray tag of the wrong kind (lamed has one imperative) would otherwise split the entry by stem
    if isinstance(code, VerbMorphCode) != (part_of_speech == "Verb"):
        return None
    match code:
        case VerbMorphCode():
            return _verb_slot(code)
        case NounMorphCode() | AdjectiveMorphCode():
            return _nominal_slot(code)
        case _:
            return _other_slot(
                code,
                "pronominal-contraction"
                if part_of_speech == "Preposition"
                else "forms",
            )


def _suffix_id(code: MorphCode) -> Maybe[SuffixId]:
    if not isinstance(code, SuffixMorphCode) or code.typ is not SuffixTypes.Pronominal:
        return None
    if code.person is None or code.gender is None or code.number is None:
        return None
    gender = "c" if code.gender in (Gender.Common, Gender.Both) else code.gender.value
    try:
        return SuffixId(f"{code.person.value}{gender}{code.number.value}")
    except ValueError:
        return None


@dataclass(frozen=True)
class ParsedUsage:
    """A whole usage code split into the word's own code and, if it has one, its pronominal suffix."""

    own: MorphCode
    # Directional he and paragogic nun/he only lengthen the word, so a form with them still fills its slot
    suffix: Maybe[SuffixId]


def parse_usage(usage: str) -> Maybe[ParsedUsage]:
    language = Language(usage[0])
    codes = [parse_code(segment, language) for segment in usage[1:].split("/")]
    if not codes or any(code is None for code in codes):
        return None
    own, *rest = codes
    if any(not isinstance(code, SuffixMorphCode) for code in rest):
        return None
    pronominal = [code for code in rest if code.typ is SuffixTypes.Pronominal]
    if len(pronominal) > 1:
        return None
    if not pronominal:
        return ParsedUsage(own, None)
    suffix = _suffix_id(pronominal[0])
    return ParsedUsage(own, suffix) if suffix is not None else None


def split_suffix(form: str, suffix_id: SuffixId) -> tuple[str, str]:
    """Split an attested suffixed form into base and suffix, trying both the verbal and nominal suffix spellings."""
    clusters = split_clusters(form)
    option = SUFFIX_OPTIONS[suffix_id]
    for spelling in dict.fromkeys([option.verb, option.noun]):
        letters = [bare_consonant(cluster) for cluster in split_clusters(spelling)]
        if (
            0 < len(letters) < len(clusters)
            and [bare_consonant(c) for c in clusters[-len(letters) :]] == letters
        ):
            return "".join(clusters[: -len(letters)]), "".join(
                clusters[-len(letters) :]
            )
    return form, ""


def format_references(refs: list[str]) -> tuple[str, ...]:
    ordered = sorted(dict.fromkeys(refs), key=oshb_sort_key)
    shown = tuple(format_oshb_ref(ref) for ref in ordered[:MAX_REFERENCES])
    if len(ordered) > MAX_REFERENCES:
        return (*shown, f"+{len(ordered) - MAX_REFERENCES} more")
    return shown


def _ranked(variants: list[FormRecord]) -> list[FormRecord]:
    """Spellings of one slot, most frequent first, with repeated spellings merged."""
    merged: dict[str, FormRecord] = {}
    for variant in variants:
        known = merged.get(variant.text)
        merged[variant.text] = (
            variant
            if known is None
            else FormRecord(
                variant.text, known.count + variant.count, known.refs + variant.refs
            )
        )
    return sorted(merged.values(), key=lambda v: -v.count)


@dataclass
class _GroupForms:
    """Forms collected for each row of a group before choosing the best source for each."""

    stem: Maybe[str]
    rows: dict[str, tuple[_Slot, list[FormRecord]]] = field(default_factory=dict)
    suffixed: dict[tuple[str, SuffixId], list[FormRecord]] = field(default_factory=dict)
    # Generated forms for rows the Bible has no plain form of
    reconstructed: dict[str, str] = field(default_factory=dict)
    count: int = 0


def _group_meta(group_id: str) -> tuple[str, str]:
    for conjugation, label, description, _ in _CONJUGATIONS:
        if conjugation == group_id:
            return label, description
    if group_id == "pronominal-contraction":
        return (
            "Forms",
            "The preposition alone, with the article, and contracted with pronominal suffixes.",
        )
    for state_id, label, description in _STATES.values():
        if state_id == group_id:
            return label, description
    return group_id.title(), ""


def _reconstruct(
    verb: VerbRoot,
    lemma: LemmaMorphology,
    collected: dict[tuple[Maybe[str], str], _GroupForms],
) -> None:
    """Fill the missing cells of each stem the verb is attested in with generated forms."""
    stems: set[str] = set()
    # The generator fits to plain forms only, since it makes no suffixed ones
    plain: dict[Slot, list[str]] = {}
    for usage, forms in lemma.usages.items():
        parsed = parse_usage(usage)
        if (
            parsed is None
            or not isinstance(parsed.own, VerbMorphCode)
            or not isinstance(parsed.own.stem, VerbStemHebrew)
        ):
            continue
        stems.add(parsed.own.stem.value)
        cell = slot_of(parsed.own) if parsed.suffix is None else None
        if cell is not None:
            plain.setdefault(cell, []).extend(form.text for form in forms)

    for stem in sorted(stems & SUPPORTED_STEMS):
        for cell, generated in reconstruct(verb, stem, plain).items():
            slot = _verb_slot(code_of(cell))
            if slot is None:
                continue
            group = collected.setdefault(
                (slot.stem, slot.group), _GroupForms(slot.stem)
            )
            _, attested = group.rows.setdefault(slot.label, (slot, []))
            # A construct participle shares its absolute's row, which then has a form already
            if not attested:
                group.reconstructed[slot.label] = generated


# The OSHB writes a sequential form's ו apart, as a conjunction, so it is put back for display
_SPELLINGS: dict[str, Callable[[str], str]] = {
    "sequential-perfect": with_conjunction,
    "sequential-imperfect": lambda form: with_conjunction(form, consecutive=True),
}


def morphology_groups(
    lemma: LemmaMorphology, part_of_speech: str, verb: Maybe[VerbRoot] = None
) -> tuple[list[MorphologyGroup], dict[tuple[str, SuffixId], ResolvedForm]]:
    collected: dict[tuple[Maybe[str], str], _GroupForms] = {}
    for usage, forms in lemma.usages.items():
        parsed = parse_usage(usage)
        if parsed is None:
            continue
        slot = _slot(parsed.own, part_of_speech)
        if slot is None:
            continue
        group = collected.setdefault((slot.stem, slot.group), _GroupForms(slot.stem))
        group.count += sum(form.count for form in forms)
        if parsed.suffix is not None:
            group.suffixed.setdefault((slot.label, parsed.suffix), []).extend(forms)
            group.rows.setdefault(slot.label, (slot, []))
        else:
            best, variants = group.rows.get(slot.label, (slot, []))
            if slot.rank < best.rank or not variants:
                group.rows[slot.label] = (slot, list(forms))
            elif slot.rank == best.rank:
                variants.extend(forms)

    if verb is not None:
        _reconstruct(verb, lemma, collected)

    stem_counts: dict[Maybe[str], int] = {}
    for (stem, _), group in collected.items():
        stem_counts[stem] = stem_counts.get(stem, 0) + group.count
    group_order = (
        [g for g, *_ in _CONJUGATIONS]
        + ["pronominal-contraction"]
        + [s[0] for s in _STATES.values()]
    )

    groups: list[MorphologyGroup] = []
    suffixed_forms: dict[tuple[str, SuffixId], ResolvedForm] = {}
    keys = sorted(
        collected, key=lambda k: (-stem_counts[k[0]], group_order.index(k[1]))
    )
    for stem, group_id in keys:
        forms = collected[(stem, group_id)]
        spell = _SPELLINGS.get(group_id, str)
        rows: list[MorphologyRow] = []
        for slot, variants in sorted(
            forms.rows.values(), key=lambda entry: entry[0].order
        ):
            ranked = _ranked(variants)
            # Unique across stems and groups, so a slot attested only with suffixes still has a key
            key = f"{stem}/{group_id}/{slot.label}"
            if ranked:
                total = sum(v.count for v in ranked)
                rows.append(
                    MorphologyRow(
                        label=slot.label,
                        form=spell(ranked[0].text),
                        transliteration="",
                        attestation=Attestation.ATTESTED,
                        note=f"{total} occurrence{'s' if total != 1 else ''}",
                        alternative=spell(ranked[1].text) if len(ranked) > 1 else None,
                        references=format_references(ranked[0].refs),
                        key=key,
                    )
                )
            elif slot.label in forms.reconstructed:
                with_suffixes = any(
                    (slot.label, suffix_id) in forms.suffixed for suffix_id in SuffixId
                )
                note = (
                    "Reconstructed · attested with suffixes"
                    if with_suffixes
                    else "Reconstructed"
                )
                rows.append(
                    MorphologyRow(
                        slot.label,
                        spell(forms.reconstructed[slot.label]),
                        "",
                        Attestation.UNATTESTED,
                        note,
                        key=key,
                    )
                )
            else:
                rows.append(
                    MorphologyRow(
                        slot.label,
                        "",
                        "",
                        Attestation.UNATTESTED,
                        note="Only with suffixes",
                        key=key,
                    )
                )
            for suffix_id in SuffixId:
                suffixed = _ranked(forms.suffixed.get((slot.label, suffix_id), []))
                if suffixed:
                    text = spell(suffixed[0].text)
                    base, suffix = split_suffix(text, suffix_id)
                    suffixed_forms[(key, suffix_id)] = ResolvedForm(
                        base,
                        suffix,
                        text,
                        "",
                        Attestation.ATTESTED,
                        format_references(suffixed[0].refs),
                    )
        label, description = _group_meta(group_id)
        groups.append(MorphologyGroup(group_id, label, description, rows, stem))
    return groups, suffixed_forms


_STRONG_PARTS_OF_SPEECH = {
    "v": "Verb",
    "n": "Noun",
    "a": "Adjective",
    "adv": "Adverb",
    "prep": "Preposition",
    "conj": "Conjunction",
    "pron": "Pronoun",
    "inj": "Interjection",
}


def part_of_speech(
    lemma: Maybe[LemmaMorphology], strong: Maybe[StrongLexiconEntry]
) -> str:
    pos = lemma.pos if lemma else None
    if not pos and lemma and lemma.usages:
        pos = next(iter(lemma.usages))[1:]
    if (pos and pos.startswith("Np")) or (
        strong and (strong.lang == "x-pn" or "n-pr" in strong.pos)
    ):
        return "Proper name"
    if pos:
        try:
            return PartOfSpeech(pos[0]).name
        except ValueError:
            pass
    if strong:
        return _STRONG_PARTS_OF_SPEECH.get(
            strong.pos.split("-")[0], strong.pos or "Word"
        )
    return "Word"


def _category(lang: str, part_of_speech: str) -> tuple[Category, Maybe[str]]:
    if part_of_speech == "Proper name":
        return Category.PROPER_NAME, "Name"
    if lang.split() == ["arc"]:
        return Category.ARAMAIC, "Aramaic"
    if part_of_speech == "Preposition":
        return Category.PREPOSITION, None
    return Category.HEBREW, None


def _language(lang: str) -> str:
    names = {"heb": "Hebrew", "arc": "Aramaic"}
    return " and ".join(names.get(part, part) for part in lang.split())


def _sentence(value: str) -> str:
    return value[:1].upper() + value[1:]


def lemma_result(
    strong_id: str,
    strong: Maybe[StrongLexiconEntry],
    lemma: Maybe[LemmaMorphology],
    root: Maybe[str],
) -> LexicalResult:
    """One lexical possibility from a Strong's entry and, when there is one, the OSHB lemma filed under it."""
    pos = part_of_speech(lemma, strong)
    lang = (
        lemma.lang if lemma else ("arc" if strong and strong.lang == "arc" else "heb")
    )
    category, category_label = _category(lang, pos)
    verb = (
        verb_root(root, lemma.lemma)
        if lemma and lemma.lemma and pos == "Verb" and lang == "heb"
        else None
    )
    groups, suffixed_forms = morphology_groups(lemma, pos, verb) if lemma else ([], {})

    gloss = (lemma.gloss if lemma else None) or (
        strong.defs[0] if strong and strong.defs else ""
    )
    properties = [Property("Root", root, hebrew=True)] if root else []
    if verb is not None:
        properties.append(Property("Verb class", verb.label))
    properties.append(Property("Language", _language(lang)))
    stems = list(dict.fromkeys(group.stem for group in groups if group.stem))
    if stems:
        properties.append(Property("Stems", ", ".join(stems)))
    if lemma:
        properties.append(Property("Occurrences", f"{lemma.count:,}"))
    # Split entries name their lemma ("H122a"); prefix lemmas such as "l" have no number of their own
    lexicon_id = f"H{lemma.key}" if lemma and lemma.key[0].isdigit() else strong_id
    properties.append(Property("Lexicon no.", lexicon_id))

    return LexicalResult(
        id=lexicon_id,
        part_of_speech=pos,
        category=category,
        lemma=(lemma.lemma if lemma else None) or (strong.lemma if strong else ""),
        transliteration=(lemma.xlit if lemma else None)
        or (strong.xlit if strong else ""),
        short_definition=_sentence(gloss),
        long_definition=_sentence(strong.meaning)
        if strong and strong.meaning
        else _sentence(gloss),
        properties=properties,
        morphology=groups,
        category_label=category_label,
        suffixed_forms=suffixed_forms,
        reconstruct_suffixes=False,
        strong_number=strong_id.removeprefix("H"),
        occurrences=lemma.count if lemma else None,
    )


def _results(backend: Backend, strong_numbers: Iterable[Strong]) -> list[LexicalResult]:
    """A lexical possibility for each lemma filed under each Strong's number, in the order given."""
    results: dict[str, LexicalResult] = {}
    for strong_number in strong_numbers:
        strong_id = f"H{strong_number.index}"
        entry = backend.get_lexicon_entry(strong_number)
        lemmas = backend.get_morphology(strong_number)
        found = (
            [lemma_result(strong_id, entry, lemma, backend.root(lemma)) for lemma in lemmas]
            if lemmas
            else [lemma_result(strong_id, entry, None, None)]
        )
        # A split entry's lemmas can each be found on their own as well as under the plain number
        for result in found:
            results.setdefault(result.id, result)
    return list(results.values())


def make_lookup(backend: Backend, n: int = 8) -> Callable[[str], list[LexicalResult]]:
    """English query -> lexical possibilities, cached because the page asks again on every option change."""

    @lru_cache(maxsize=256)
    def cached(query: str) -> list[LexicalResult]:
        return _results(backend, backend.search_string(query, n))

    return lambda query: cached(" ".join(query.lower().split()))


def make_hebrew_lookup(backend: Backend, n: int = 8) -> Callable[[str], list[LexicalResult]]:
    """Hebrew word -> the lemmas spelled most like it, cached like :func:`make_lookup`."""

    @lru_cache(maxsize=256)
    def cached(query: str) -> list[LexicalResult]:
        return _results(backend, backend.search_hebrew(query, n))

    return lambda query: cached(query.strip())
