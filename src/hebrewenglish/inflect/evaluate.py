"""Measure how often the generator reproduces the forms the Bible attests.

Run with ``python -m hebrewenglish.inflect.evaluate [--misses N]``. Each attested plain verb form in a supported
stem is generated twice: from the default parameters, and from parameters fitted to the lemma's own forms in
that stem. The fitted figure is optimistic, since the form under test also informs the fit.
"""

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from hebrewenglish.common.maybe import Maybe
from hebrewenglish.lexicon.morphs.codes import Language, VerbMorphCode, parse_code

from .generate import Slot, default_params, fit, slot_of
from .letters import comparable
from .paradigm import generate
from .roots import VerbRoot, verb_root

_RESOURCES = Path(__file__).resolve().parents[1] / "lexicon" / "res"


@dataclass(frozen=True)
class AttestedVerb:
    key: str
    lemma: str
    root: VerbRoot
    # Plain forms (no suffixes) per cell, most frequent spelling first
    forms: dict[Slot, list[str]]


def attested_slots(usages: dict[str, list[str]]) -> dict[Slot, list[str]]:
    """Group a lemma's plain usage codes (``HVqp3ms``, no suffix segment) into paradigm cells."""
    forms: dict[Slot, list[str]] = defaultdict(list)
    for usage, texts in usages.items():
        if "/" in usage or not usage.startswith("HV"):
            continue
        code = parse_code(usage[1:], Language.Hebrew)
        if not isinstance(code, VerbMorphCode):
            continue
        slot = slot_of(code)
        if slot is not None:
            forms[slot].extend(texts)
    return dict(forms)


def load_verbs() -> Iterator[AttestedVerb]:
    lemmas = json.loads((_RESOURCES / "morph.json").read_text())["lemmas"]
    index = json.loads((_RESOURCES / "index.json").read_text())
    for key, record in lemmas.items():
        if (
            not (record.get("pos") or "").startswith("V")
            or record.get("lang") != "heb"
            or not record.get("lemma")
        ):
            continue
        root = verb_root(
            index.get(record.get("index") or "", {}).get("root"), record["lemma"]
        )
        if root is None:
            continue
        usages = {
            usage: [
                form["text"]
                for form in sorted(data["forms"], key=lambda f: -f["count"])
            ]
            for usage, data in record["usages"].items()
        }
        yield AttestedVerb(key, record["lemma"], root, attested_slots(usages))


@dataclass(frozen=True)
class Trial:
    """One attested cell, generated from the default parameters and from those fitted to the lemma's stem."""

    verb: AttestedVerb
    slot: Slot
    default: Maybe[str]
    fitted: Maybe[str]

    def matches(self, form: Maybe[str]) -> bool:
        return form is not None and comparable(form) in {
            comparable(text) for text in self.verb.forms[self.slot]
        }


def trials(
    verbs: Iterable[AttestedVerb], only_stem: Maybe[str] = None
) -> Iterator[Trial]:
    for verb in verbs:
        for stem in sorted({slot.stem for slot in verb.forms}):
            if only_stem and stem != only_stem:
                continue
            default, fitted = (
                default_params(verb.root),
                fit(verb.root, stem, verb.forms),
            )
            for slot in verb.forms:
                if slot.stem == stem:
                    yield Trial(
                        verb,
                        slot,
                        generate(verb.root, stem, slot.typ, slot.cell, default),
                        generate(verb.root, stem, slot.typ, slot.cell, fitted),
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--misses",
        type=int,
        default=25,
        help="how many of the commonest misses to list",
    )
    parser.add_argument("--stem", help="only this OSHB stem letter")
    parser.add_argument(
        "--klass", help="only roots whose class label contains this text"
    )
    args = parser.parse_args()

    totals: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    misses: Counter[tuple[str, str, str]] = Counter()
    examples: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    verbs = (
        verb for verb in load_verbs() if not args.klass or args.klass in verb.root.label
    )
    for trial in trials(verbs, args.stem):
        label, slot = trial.verb.root.label, trial.slot
        count = totals[(label, slot.stem)]
        count["cells"] += 1
        count["default"] += trial.matches(trial.default)
        count["fitted"] += trial.matches(trial.fitted)
        count["none"] += trial.fitted is None
        if trial.fitted is not None and not trial.matches(trial.fitted):
            kind = (label, slot.stem, slot.typ + slot.cell)
            misses[kind] += 1
            examples[kind].append(
                f"{trial.verb.lemma}: {trial.fitted} ≠ {trial.verb.forms[slot][0]}"
            )

    print(f"{'class':<28}{'stem':<6}{'cells':>7}{'default':>9}{'fitted':>9}{'none':>7}")
    overall: Counter[str] = Counter()
    for (label, stem), count in sorted(
        totals.items(), key=lambda item: -item[1]["cells"]
    ):
        overall.update(count)
        cells = count["cells"]
        print(
            f"{label:<28}{stem:<6}{cells:>7}{count['default'] / cells:>9.1%}{count['fitted'] / cells:>9.1%}"
            f"{count['none'] / cells:>7.1%}"
        )
    cells = overall["cells"] or 1
    print(
        f"{'all':<34}{cells:>7}{overall['default'] / cells:>9.1%}{overall['fitted'] / cells:>9.1%}"
    )
    if args.misses:
        print("\ncommonest misses (class, stem, cell): examples")
        for kind, n in misses.most_common(args.misses):
            print(f"{n:>5} {kind}: {'; '.join(examples[kind][:3])}")


if __name__ == "__main__":
    main()
