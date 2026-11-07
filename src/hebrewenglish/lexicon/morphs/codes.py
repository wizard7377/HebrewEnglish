from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum

from hebrewenglish.common.maybe import Maybe


class CodePart:
    @abstractmethod
    def write(self) -> str:
        pass


class CodeEnum(CodePart, Enum):
    def write(self) -> str:
        return self.value


class Language(CodeEnum):
    Hebrew = "H"
    Aramaic = "A"


class PartOfSpeech(CodeEnum):
    Adjective = "A"
    Conjunction = "C"
    Adverb = "D"
    Noun = "N"
    Pronoun = "P"
    Preposition = "R"
    Suffix = "S"
    Particle = "T"
    Verb = "V"


class VerbStemHebrew(CodeEnum):
    Qal = "q"
    Niphal = "N"
    Piel = "p"
    Pual = "P"
    Hiphil = "h"
    Hophal = "H"
    Hithpael = "t"
    Polel = "o"
    Polal = "O"
    Hithpolel = "r"
    Poel = "m"
    Poal = "M"
    Palel = "k"
    Pulal = "K"
    QalPassive = "Q"
    Pilpel = "l"
    Polpal = "L"
    Hithpalpel = "f"
    Nithpael = "D"
    Pealal = "j"
    Pilel = "i"
    Hothpaal = "u"
    Tiphil = "c"
    Hishtaphel = "v"
    Nithpalel = "w"
    Nithpoel = "y"
    Hithpoel = "z"


class VerbStemAramaic(CodeEnum):
    Peal = "q"
    Peil = "Q"
    Hithpeel = "u"
    Pael = "p"
    Ithpaal = "P"
    Hithpaal = "M"
    Aphel = "a"
    Haphel = "h"
    Saphel = "s"
    Shaphel = "e"
    Hophal = "H"
    Ithpeel = "i"
    Hishtaphel = "t"
    Ishtaphel = "v"
    Hithaphel = "w"
    Polel = "o"
    Ithpoel = "z"
    Hithpolel = "r"
    Hithpalpel = "f"
    Hephal = "b"
    Tiphel = "c"
    Poel = "m"
    Palpel = "l"
    Ithpalpel = "L"
    Ithpolel = "O"
    Ittaphal = "G"


class VerbTypes(CodeEnum):
    SimplePerfect = "p"
    SequentialPerfect = "q"
    Imperfect = "i"
    SequentialImperfect = "w"
    Cohortative = "h"
    Jussive = "j"
    Imperative = "v"
    ActiveParticiple = "r"
    PassiveParticiple = "s"
    InfinitiveAbsolute = "a"
    InfinitiveConstruct = "c"


class AdjectiveTypes(CodeEnum):
    Absolute = "a"
    Cardinal = "c"
    Gentilic = "g"
    Ordinal = "o"


class NounTypes(CodeEnum):
    Common = "c"
    Gentilic = "g"
    Proper = "p"


class PronounTypes(CodeEnum):
    Demonstrative = "d"
    Indefinite = "f"
    Interrogative = "i"
    Personal = "p"
    Relative = "r"


class PrepositionTypes(CodeEnum):
    DefiniteArticle = "d"


class SuffixTypes(CodeEnum):
    DirectionalHe = "d"
    ParagogicHe = "h"
    ParagogicNun = "n"
    Pronominal = "p"


class ParticleTypes(CodeEnum):
    Affirmation = "a"
    DefiniteArticle = "d"
    Exhortation = "e"
    Interrogative = "i"
    Interjection = "j"
    Demonstrative = "m"
    Negative = "n"
    DirectObjectMarker = "o"
    Relative = "r"


class Person(CodeEnum):
    First = "1"
    Second = "2"
    Third = "3"


class Gender(CodeEnum):
    Both = "b"
    Common = "c"
    Feminine = "f"
    Masculine = "m"


class Number(CodeEnum):
    Dual = "d"
    Plural = "p"
    Singular = "s"


class State(CodeEnum):
    Absolute = "a"
    Construct = "c"
    Determined = "d"


@dataclass(frozen=True)
class AdjectiveMorphCode(CodePart):
    typ: Maybe[AdjectiveTypes]
    gender: Maybe[Gender]
    number: Maybe[Number]
    state: Maybe[State]

    def write(self) -> str:
        return write_parts(
            [PartOfSpeech.Adjective, self.typ, self.gender, self.number, self.state]
        )


@dataclass(frozen=True)
class ConjunctionMorphCode(CodePart):
    def write(self) -> str:
        return write_parts([PartOfSpeech.Conjunction])


@dataclass(frozen=True)
class AdverbMorphCode(CodePart):
    def write(self) -> str:
        return write_parts([PartOfSpeech.Adverb])


@dataclass(frozen=True)
class NounMorphCode(CodePart):
    typ: Maybe[NounTypes]
    gender: Maybe[Gender]
    number: Maybe[Number]
    state: Maybe[State]

    def write(self) -> str:
        return write_parts(
            [PartOfSpeech.Noun, self.typ, self.gender, self.number, self.state]
        )


@dataclass(frozen=True)
class PronounMorphCode(CodePart):
    typ: Maybe[PronounTypes]
    person: Maybe[Person]
    gender: Maybe[Gender]
    number: Maybe[Number]

    def write(self) -> str:
        return write_parts(
            [PartOfSpeech.Pronoun, self.typ, self.person, self.gender, self.number]
        )


@dataclass(frozen=True)
class PrepositionMorphCode(CodePart):
    typ: Maybe[PrepositionTypes]

    def write(self) -> str:
        return write_parts([PartOfSpeech.Preposition, self.typ])


@dataclass(frozen=True)
class SuffixMorphCode(CodePart):
    typ: Maybe[SuffixTypes]
    person: Maybe[Person]
    gender: Maybe[Gender]
    number: Maybe[Number]

    def write(self) -> str:
        return write_parts(
            [PartOfSpeech.Suffix, self.typ, self.person, self.gender, self.number]
        )


@dataclass(frozen=True)
class ParticleMorphCode(CodePart):
    typ: Maybe[ParticleTypes]

    def write(self) -> str:
        return write_parts([PartOfSpeech.Particle, self.typ])


@dataclass(frozen=True)
class VerbMorphCode(CodePart):
    stem: Maybe[VerbStemHebrew | VerbStemAramaic]
    typ: Maybe[VerbTypes]
    person: Maybe[Person]
    gender: Maybe[Gender]
    number: Maybe[Number]
    state: Maybe[State]

    def write(self) -> str:
        # Participles have no person slot at all, so no "x" is written for it
        if self.typ in (VerbTypes.ActiveParticiple, VerbTypes.PassiveParticiple):
            return write_parts(
                [
                    PartOfSpeech.Verb,
                    self.stem,
                    self.typ,
                    self.gender,
                    self.number,
                    self.state,
                ]
            )
        return write_parts(
            [
                PartOfSpeech.Verb,
                self.stem,
                self.typ,
                self.person,
                self.gender,
                self.number,
                self.state,
            ]
        )


type MorphCode = (
    AdjectiveMorphCode
    | ConjunctionMorphCode
    | AdverbMorphCode
    | NounMorphCode
    | PronounMorphCode
    | PrepositionMorphCode
    | SuffixMorphCode
    | ParticleMorphCode
    | VerbMorphCode
)


def write_part(part: Maybe[CodePart]) -> str:
    if part is not None:
        return part.write()
    else:
        return "x"


def write_parts(parts: list[Maybe[CodePart]]) -> str:
    res = "".join([write_part(part) for part in parts])
    while res.endswith("x"):
        res = res[:-1]
    return res


def parse_part[T: CodeEnum](enum: type[T], code: str, index: int) -> Maybe[T]:
    part = code[index : index + 1]
    if part in ("", "x"):
        return None
    return enum(part)


def parse_verb(code: str, language: Language) -> VerbMorphCode:
    stems = VerbStemHebrew if language is Language.Hebrew else VerbStemAramaic
    stem = parse_part(stems, code, 1)
    typ = parse_part(VerbTypes, code, 2)
    # Participles have no person slot at all, so the rest sits one place earlier
    if typ in (VerbTypes.ActiveParticiple, VerbTypes.PassiveParticiple):
        return VerbMorphCode(
            stem,
            typ,
            None,
            parse_part(Gender, code, 3),
            parse_part(Number, code, 4),
            parse_part(State, code, 5),
        )
    return VerbMorphCode(
        stem,
        typ,
        parse_part(Person, code, 3),
        parse_part(Gender, code, 4),
        parse_part(Number, code, 5),
        parse_part(State, code, 6),
    )


def parse_parts(code: str, language: Language) -> MorphCode:
    match PartOfSpeech(code[:1]):
        case PartOfSpeech.Adjective:
            return AdjectiveMorphCode(
                parse_part(AdjectiveTypes, code, 1),
                parse_part(Gender, code, 2),
                parse_part(Number, code, 3),
                parse_part(State, code, 4),
            )
        case PartOfSpeech.Conjunction:
            return ConjunctionMorphCode()
        case PartOfSpeech.Adverb:
            return AdverbMorphCode()
        case PartOfSpeech.Noun:
            return NounMorphCode(
                parse_part(NounTypes, code, 1),
                parse_part(Gender, code, 2),
                parse_part(Number, code, 3),
                parse_part(State, code, 4),
            )
        case PartOfSpeech.Pronoun:
            return PronounMorphCode(
                parse_part(PronounTypes, code, 1),
                parse_part(Person, code, 2),
                parse_part(Gender, code, 3),
                parse_part(Number, code, 4),
            )
        case PartOfSpeech.Preposition:
            return PrepositionMorphCode(parse_part(PrepositionTypes, code, 1))
        case PartOfSpeech.Suffix:
            return SuffixMorphCode(
                parse_part(SuffixTypes, code, 1),
                parse_part(Person, code, 2),
                parse_part(Gender, code, 3),
                parse_part(Number, code, 4),
            )
        case PartOfSpeech.Particle:
            return ParticleMorphCode(parse_part(ParticleTypes, code, 1))
        case PartOfSpeech.Verb:
            return parse_verb(code, language)


def parse_code(code: str, language: Language) -> Maybe[MorphCode]:
    """
    Parses one segment of a morphology code, such as the "Sp3ms" in "HR/Sp3ms".

    Only the start of a whole code names its language, so it is removed first and passed in.
    """
    try:
        parsed = parse_parts(code, language)
    except ValueError:
        return None
    # Whatever write does not reproduce was left over after the last slot
    return parsed if parsed.write() == code else None
