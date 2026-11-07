from hebrewenglish.common.maybe import Maybe
from src.hebrewenglish.lexicon.group import LexicalGroup


class Gloss:
    text: str
    usage: Maybe[str]
    group: LexicalGroup

    def __init__(self, text: str, group: LexicalGroup, usage: Maybe[str] = None):
        self.text = text
        self.group = group
        self.usage = usage
