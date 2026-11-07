import math
from dataclasses import dataclass, field

import numpy as np
from model2vec import StaticModel


@dataclass
class LexicalElement:
    definition: str
    sense: str
    pos: str
    lang: str = "heb"
    glosses: list[str] = field(default_factory=list)
    usages: list[str] = field(default_factory=list)


class Matcher:
    _word_list: list[LexicalElement]
    _model: StaticModel

    def __init__(
        self,
        word_list: list[LexicalElement],
        model: StaticModel,
        proper_noun_factor: float = 0.5,
        usage_factor: float = 0.7,
        aramaic_factor: float = 0.9,
        popularity_factor: float = 0.05,
    ):
        self._word_list = word_list
        self._model = model
        # Each sense gets its own row, as averaging a long definition's words blurs it away from any one of them.
        texts: list[str] = []
        owners: list[int] = []
        factors: list[float] = []
        for i, element in enumerate(word_list):
            weight = 1.0 + popularity_factor * math.log1p(len(element.usages))
            # Some common words, such as H1419 "great", are also names, and those keep their full score.
            tags = element.pos.split()
            if tags and all("n-pr" in tag for tag in tags):
                weight *= proper_noun_factor
            if element.lang == "arc":
                weight *= aramaic_factor
            glosses = (
                element.glosses
                if element.glosses or element.usages
                else [element.definition]
            )
            for text, factor in [(g, weight) for g in glosses] + [
                (u, weight * usage_factor) for u in element.usages
            ]:
                texts.append(text)
                owners.append(i)
                factors.append(factor)
        self._owners = np.array(owners)
        # normalize is explicit because the model may have been loaded without it.
        self._vectors = model.encode(texts, normalize=True)
        # Scaling a vector scales its dot products, and so its scores, by the same factor.
        self._vectors *= np.array(factors, dtype=self._vectors.dtype)[:, np.newaxis]

    def get_matches(self, word: str, n: int = 4) -> list[tuple[int, LexicalElement]]:
        """
        Returns the n elements whose best senses best match the word, best match first.
        """
        # The vectors are normalized, so their dot products are cosine similarities, scaled by their factors.
        sense_scores = self._vectors @ self._model.encode(word, normalize=True)
        scores = np.full(len(self._word_list), -np.inf)
        np.maximum.at(scores, self._owners, sense_scores)
        return [(i, self._word_list[i]) for i in (-scores).argsort()[:n]]
