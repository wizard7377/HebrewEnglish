"""Book names for OSHB references such as "Gen.2.24", in the canon order of English Bibles."""

OSHB_BOOKS: dict[str, str] = {
    "Gen": "Genesis",
    "Exod": "Exodus",
    "Lev": "Leviticus",
    "Num": "Numbers",
    "Deut": "Deuteronomy",
    "Josh": "Joshua",
    "Judg": "Judges",
    "Ruth": "Ruth",
    "1Sam": "1 Samuel",
    "2Sam": "2 Samuel",
    "1Kgs": "1 Kings",
    "2Kgs": "2 Kings",
    "1Chr": "1 Chronicles",
    "2Chr": "2 Chronicles",
    "Ezra": "Ezra",
    "Neh": "Nehemiah",
    "Esth": "Esther",
    "Job": "Job",
    # One verse at a time, so the singular
    "Ps": "Psalm",
    "Prov": "Proverbs",
    "Eccl": "Ecclesiastes",
    "Song": "Song of Songs",
    "Isa": "Isaiah",
    "Jer": "Jeremiah",
    "Lam": "Lamentations",
    "Ezek": "Ezekiel",
    "Dan": "Daniel",
    "Hos": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obad": "Obadiah",
    "Jonah": "Jonah",
    "Mic": "Micah",
    "Nah": "Nahum",
    "Hab": "Habakkuk",
    "Zeph": "Zephaniah",
    "Hag": "Haggai",
    "Zech": "Zechariah",
    "Mal": "Malachi",
}

_ORDER = {book: index for index, book in enumerate(OSHB_BOOKS)}


def oshb_sort_key(ref: str) -> tuple[int, int, int]:
    book, chapter, verse = ref.split(".")
    return _ORDER.get(book, len(_ORDER)), int(chapter), int(verse)


def format_oshb_ref(ref: str) -> str:
    """ "Gen.2.24" -> "Genesis 2:24"; an unknown book keeps its abbreviation."""
    book, chapter, verse = ref.split(".")
    return f"{OSHB_BOOKS.get(book, book)} {chapter}:{verse}"
