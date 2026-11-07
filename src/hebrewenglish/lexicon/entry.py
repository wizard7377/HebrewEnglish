from abc import abstractmethod

from hebrewenglish.common.strong import Strong
from hebrewenglish.lexicon.gloss import Gloss
from src.hebrewenglish.common.maybe import Maybe


class LexiconEntry:
    @abstractmethod
    def strong_number(self) -> Strong:
        pass

    @abstractmethod
    def bdb_number(self) -> int:
        pass

    def oshb_tag(self) -> Maybe[str]:
        return None

    @abstractmethod
    def citation_form(self) -> str:
        pass

    @abstractmethod
    def glosses(self) -> list[Gloss]:
        return []


class StrongEntry(LexiconEntry):
    _strong_number: Strong

    def __init__(self, strong_number: Strong):
        self._strong_number = strong_number

    def strong_number(self) -> Strong:
        return self._strong_number

