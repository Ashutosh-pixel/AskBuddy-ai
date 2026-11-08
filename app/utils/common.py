import re


VAGUE_REF = re.compile(
    r"\b(it|its|that|those|these|them|both|above|same|again|"
    r"previously|earlier|latter|former|the two|the ones)\b",
    re.IGNORECASE,
)

def _history_for_answer(user_query: str, chat_history: list[dict]) -> list[dict]:
    if VAGUE_REF.search(user_query):
        return chat_history[-4:]
    return []   # self-contained query → no history