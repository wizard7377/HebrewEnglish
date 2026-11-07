from dataclasses import dataclass


@dataclass
class All:
    pass


type Group = int | tuple[int, int] | list[Group] | All


@dataclass
class BibleCite:
    book: str
    chapter: Group
    verse: Group


type Cite = BibleCite


def parse_group(group_str: str) -> Group:
    if group_str == "*":
        return All()
    elif "-" in group_str:
        start, end = group_str.split("-")
        return (int(start), int(end))
    elif "," in group_str:
        return [parse_group(part) for part in group_str.split(",")]
    else:
        return int(group_str)


def cite_from_oshb(cite_str: str) -> Cite:
    parts = cite_str.split(".")
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError(f"Invalid cite string: {cite_str}")
    elif len(parts) == 2:
        book, chapter_str = parts
        chapter = parse_group(chapter_str)
        verse = All()
        return BibleCite(book=book, chapter=chapter, verse=verse)
    else:
        book, chapter_str, verse_str = parts
        chapter = parse_group(chapter_str)
        verse = parse_group(verse_str)
        return BibleCite(book=book, chapter=chapter, verse=verse)
