from app.utils.normalize_utils import normalize
from difflib import SequenceMatcher

def resolve_doc(name: str, available: list[dict]) -> dict:
    """
    Returns one of:
      {"status": "ok",       "doc": "<filename>"}
      {"status": "ambiguous","doc": [<filename>, ...]}
      {"status": "not_found","doc": []}
    """

    if not any(item == name for item in available):
        return {"status": "not_found", "doc": []}

    target = normalize(name)

    # ---- Tier 1: exact normalized match ----
    exact = [doc for doc in available if normalize(doc) == target]
    if len(exact) == 1:
        return {"status": "ok", "doc": exact[0]}
    if len(exact) > 1:
        return {"status": "ambiguous", "doc": exact}

    # ---- Tier 2: fuzzy score ----
    scored = sorted(
        ((d, SequenceMatcher(None, target, normalize(d)).ratio()) for d in available),
        key=lambda x: -x[1],
    )
    top_doc, top_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0

    # confident: high score + clear gap over runner-up
    if top_score >= 0.85 and (top_score - second_score) >= 0.15:
        return {"status": "ok", "doc": top_doc}

    # token containment (e.g. "ashu resume" ⊂ "ashu resume 2024")
    target_tokens = set(target.split())
    contained = [
        d for d in available
        if target_tokens and target_tokens.issubset(set(normalize(d).split()))
    ]
    if len(contained) == 1:
        return {"status": "ok", "doc": contained[0]}
    if len(contained) > 1:
        return {"status": "ambiguous", "doc": contained}

    # ambiguous: several plausible doc
    plausible = [d for d, s in scored if s >= 0.5]
    if len(plausible) > 1:
        return {"status": "ambiguous", "doc": plausible[:5]}

    if top_score >= 0.5:
        return {"status": "ok", "doc": top_doc}

    return {"status": "not_found", "doc": []}