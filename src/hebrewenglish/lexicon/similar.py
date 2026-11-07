"""Hebrew lemmas that look like a typed Hebrew word: the word itself, a form of it, its relatives, or a near spelling.

Everything is compared on bare consonants, so the word may be typed with or without points.
"""

from collections.abc import Iterable
from dataclasses import dataclass
import unicodedata

from hebrewenglish.common.maybe import Maybe

_FINALS = str.maketrans("ךםןףץ", "כמנפצ")
# Letters the Bible writes onto the front of a word: and, the, in, like, to, from, that
_PREFIXES = "והבכלמש"


@dataclass(frozen=True)
class IndexedLemma:
    key: str
    lemma: str
    forms: tuple[str, ...]
    root: Maybe[str]
    count: int


def consonants(word: str) -> str:
    """The letters of a word without points, final letters written as medial ones."""
    letters = "".join(c for c in unicodedata.normalize("NFD", word) if "א" <= c <= "ת")
    return letters.translate(_FINALS)


def skeleton(letters: str) -> str:
    """Consonants with ו and י dropped after the first letter, so that plene and defective spellings meet."""
    return letters[:1] + letters[1:].replace("ו", "").replace("י", "")


def _without_prefixes(letters: str) -> list[str]:
    """The word with one or two prefix letters taken off, leaving at least two letters."""
    stripped = []
    for count in (1, 2):
        head, rest = letters[:count], letters[count:]
        if len(rest) >= 2 and all(c in _PREFIXES for c in head):
            stripped.append(rest)
    return stripped


def _distance(a: str, b: str, limit: int) -> int:
    """Levenshtein distance, or ``limit + 1`` once it is sure to exceed ``limit``."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


class HebrewIndex:
    """Lemmas by the consonants of their dictionary form, their attested forms and their root."""

    def __init__(self, lemmas: Iterable[IndexedLemma]) -> None:
        self._lemmas = {lemma.key: lemma for lemma in lemmas}
        self._by_lemma: dict[str, set[str]] = {}
        self._by_form: dict[str, set[str]] = {}
        self._by_skeleton: dict[str, set[str]] = {}
        self._by_root: dict[str, set[str]] = {}
        for lemma in self._lemmas.values():
            own = consonants(lemma.lemma)
            self._by_lemma.setdefault(own, set()).add(lemma.key)
            self._by_skeleton.setdefault(skeleton(own), set()).add(lemma.key)
            for form in lemma.forms:
                letters = consonants(form)
                self._by_form.setdefault(letters, set()).add(lemma.key)
                self._by_skeleton.setdefault(skeleton(letters), set()).add(lemma.key)
            if lemma.root:
                self._by_root.setdefault(consonants(lemma.root), set()).add(lemma.key)

    def _root(self, key: str) -> Maybe[str]:
        root = self._lemmas[key].root
        return consonants(root) if root else None

    def _spelled(self, letters: str) -> list[set[str]]:
        """Lemmas spelled ``letters``: as their dictionary form, as an attested form, or but for matres."""
        return [
            self._by_lemma.get(letters, set()),
            self._by_form.get(letters, set()),
            self._by_skeleton.get(skeleton(letters), set()),
        ]

    def search(self, word: str, n: int = 8) -> list[str]:
        """Keys of the lemmas most like ``word``, best first.

        In order: lemmas the word spells, as a dictionary form, an inflected form or a plene spelling; failing
        those, the same once prefixes such as ו and ה are taken off; other words from the root of what was
        found; and, to make up the number, lemmas a letter away. More frequent words come first in each.
        """
        letters = consonants(word)
        if not letters:
            return []
        tiers = self._spelled(letters)
        stems = [letters]
        if not any(tiers):
            stems = _without_prefixes(letters)
            # By kind of match across every reading, so that the article in המלך is read before a Hiphil
            tiers = [set().union(*kind) for kind in zip(*map(self._spelled, stems))] if stems else []
        found = set().union(*tiers)
        # The typed letters may themselves be a root, as in שמר for שָׁמַר, שֹׁמֵר and מִשְׁמֶרֶת
        roots = {root for key in found if (root := self._root(key))} | set(stems)
        tiers.append(set().union(*(self._by_root.get(root, set()) for root in roots)))
        found |= tiers[-1]
        if len(found) < n:
            tiers.append(
                {
                    key
                    for key, lemma in self._lemmas.items()
                    if key not in found and _distance(letters, consonants(lemma.lemma), 1) <= 1
                }
            )

        ranked: dict[str, None] = {}
        for tier in tiers:
            ranked.update(dict.fromkeys(sorted(tier, key=lambda key: -self._lemmas[key].count)))
        return list(ranked)[:n]
