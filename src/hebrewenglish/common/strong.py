import re
from dataclasses import dataclass

from hebrewenglish.common.maybe import Maybe


@dataclass(frozen=True)
class Strong:
    index: int
    modifier: Maybe[str] = None


def parse_strong(text: str) -> Maybe[Strong]:
    match = re.fullmatch(r"(\d+)([a-z]?)", text)
    if match is None:
        return None
    return Strong(int(match[1]), match[2] or None)
