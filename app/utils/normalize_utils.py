import re

def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[_\-\.]+", " ", s)
    s = re.sub(r"\b(pdf|docx?|txt|xlsx?|pptx?)\b", "", s)
    s = re.sub(r"[^\w\s]", " ", s)          # drop punctuation (incl. apostrophes)
    s = re.sub(r"\s+", " ", s).strip()
    return s