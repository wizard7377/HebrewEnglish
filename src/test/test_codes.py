from hebrewenglish.lexicon.morphs.codes import (
    AdjectiveMorphCode,
    AdjectiveTypes,
    AdverbMorphCode,
    ConjunctionMorphCode,
    Gender,
    Language,
    NounMorphCode,
    NounTypes,
    Number,
    ParticleMorphCode,
    ParticleTypes,
    PartOfSpeech,
    Person,
    PrepositionMorphCode,
    PrepositionTypes,
    PronounMorphCode,
    PronounTypes,
    State,
    SuffixMorphCode,
    SuffixTypes,
    VerbMorphCode,
    VerbStemAramaic,
    VerbStemHebrew,
    VerbTypes,
    parse_code,
    write_parts,
)


def test_language_prefix():
    verb = VerbMorphCode(
        VerbStemHebrew.Qal,
        VerbTypes.SimplePerfect,
        Person.Third,
        Gender.Masculine,
        Number.Singular,
        None,
    )
    assert write_parts([Language.Hebrew, verb]) == "HVqp3ms"


def test_trailing_placeholders_dropped():
    assert write_parts([PartOfSpeech.Verb, VerbStemHebrew.Qal, None, None]) == "Vq"


def test_adjective():
    code = AdjectiveMorphCode(
        AdjectiveTypes.Cardinal, Gender.Both, Number.Plural, State.Absolute
    )
    assert code.write() == "Acbpa"


def test_conjunction():
    assert ConjunctionMorphCode().write() == "C"


def test_adverb():
    assert AdverbMorphCode().write() == "D"


def test_common_noun():
    code = NounMorphCode(
        NounTypes.Common, Gender.Masculine, Number.Plural, State.Absolute
    )
    assert code.write() == "Ncmpa"


def test_proper_noun_drops_unused_fields():
    assert NounMorphCode(NounTypes.Proper, None, None, None).write() == "Np"


def test_noun_with_only_a_state():
    assert NounMorphCode(None, None, None, State.Absolute).write() == "Nxxxa"


def test_personal_pronoun():
    code = PronounMorphCode(
        PronounTypes.Personal, Person.First, Gender.Common, Number.Singular
    )
    assert code.write() == "Pp1cs"


def test_demonstrative_pronoun_keeps_person_placeholder():
    code = PronounMorphCode(
        PronounTypes.Demonstrative, None, Gender.Masculine, Number.Singular
    )
    assert code.write() == "Pdxms"


def test_preposition():
    assert PrepositionMorphCode(None).write() == "R"
    assert PrepositionMorphCode(PrepositionTypes.DefiniteArticle).write() == "Rd"


def test_pronominal_suffix():
    code = SuffixMorphCode(
        SuffixTypes.Pronominal, Person.Third, Gender.Masculine, Number.Singular
    )
    assert code.write() == "Sp3ms"


def test_directional_he_suffix():
    assert SuffixMorphCode(SuffixTypes.DirectionalHe, None, None, None).write() == "Sd"


def test_particle():
    assert ParticleMorphCode(ParticleTypes.DirectObjectMarker).write() == "To"


def test_finite_verb():
    code = VerbMorphCode(
        VerbStemHebrew.Qal,
        VerbTypes.SequentialImperfect,
        Person.Third,
        Gender.Masculine,
        Number.Singular,
        None,
    )
    assert code.write() == "Vqw3ms"


def test_participle_has_no_person_slot():
    code = VerbMorphCode(
        VerbStemHebrew.Piel,
        VerbTypes.ActiveParticiple,
        None,
        Gender.Feminine,
        Number.Singular,
        State.Absolute,
    )
    assert code.write() == "Vprfsa"


def test_infinitive():
    code = VerbMorphCode(
        VerbStemHebrew.Qal, VerbTypes.InfinitiveConstruct, None, None, None, None
    )
    assert code.write() == "Vqc"


def test_aramaic_verb_stem():
    code = VerbMorphCode(
        VerbStemAramaic.Haphel,
        VerbTypes.SimplePerfect,
        Person.Third,
        Gender.Masculine,
        Number.Singular,
        None,
    )
    assert code.write() == "Vhp3ms"


def test_parse_finite_verb():
    assert parse_code("Vqw3ms", Language.Hebrew) == VerbMorphCode(
        VerbStemHebrew.Qal,
        VerbTypes.SequentialImperfect,
        Person.Third,
        Gender.Masculine,
        Number.Singular,
        None,
    )


def test_parse_participle_has_no_person_slot():
    assert parse_code("Vprfsa", Language.Hebrew) == VerbMorphCode(
        VerbStemHebrew.Piel,
        VerbTypes.ActiveParticiple,
        None,
        Gender.Feminine,
        Number.Singular,
        State.Absolute,
    )


def test_parse_verb_stem_follows_language():
    hebrew = parse_code("Vhp3ms", Language.Hebrew)
    aramaic = parse_code("Vhp3ms", Language.Aramaic)
    assert isinstance(hebrew, VerbMorphCode) and hebrew.stem is VerbStemHebrew.Hiphil
    assert isinstance(aramaic, VerbMorphCode) and aramaic.stem is VerbStemAramaic.Haphel


def test_parse_placeholders():
    assert parse_code("Nxxxa", Language.Hebrew) == NounMorphCode(
        None, None, None, State.Absolute
    )
    assert parse_code("Pdxms", Language.Hebrew) == PronounMorphCode(
        PronounTypes.Demonstrative, None, Gender.Masculine, Number.Singular
    )


def test_parse_dropped_trailing_fields():
    assert parse_code("Np", Language.Hebrew) == NounMorphCode(
        NounTypes.Proper, None, None, None
    )
    assert parse_code("C", Language.Hebrew) == ConjunctionMorphCode()
    assert parse_code("R", Language.Hebrew) == PrepositionMorphCode(None)


def test_parse_adjective_is_not_mistaken_for_aramaic():
    assert parse_code("Acbsa", Language.Aramaic) == AdjectiveMorphCode(
        AdjectiveTypes.Cardinal, Gender.Both, Number.Singular, State.Absolute
    )


def test_parse_invalid_codes():
    assert parse_code("", Language.Hebrew) is None
    assert parse_code("kind", Language.Hebrew) is None
    assert parse_code("Z", Language.Hebrew) is None
    assert parse_code("Nz", Language.Hebrew) is None
    assert parse_code("Cc", Language.Hebrew) is None
    assert parse_code("Rdd", Language.Hebrew) is None


def test_codes_are_hashable():
    code = NounMorphCode(NounTypes.Common, None, None, None)
    assert {code: 1}[NounMorphCode(NounTypes.Common, None, None, None)] == 1
