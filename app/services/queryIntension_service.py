import json
from openai import AsyncOpenAI, OpenAI

from app.prompts.rewriter_prompt import REWRITER_PROMPT

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
    )

VALID_OPERATIONS = ["search", "summarize", "compare", "chat", "metadata", "recall"]

async def route(user_query: str, history: list[dict]):
    messages = [
        {"role": "system", "content": REWRITER_PROMPT},
        *history[-4:],
        {"role": "user", "content": user_query},
    ]

    response = await client.chat.completions.create(
        model="gemma4:e2b",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )

    plan = json.loads(response.choices[0].message.content)

    return await validate(plan=plan, user_query=user_query)


async def validate(plan: dict, user_query: str) -> dict:
    op = plan.get("operation", "search")
    if op not in VALID_OPERATIONS:
        op = "search"

    # normalize queries: only non-empty strings
    raw_q = plan.get("queries", [])
    queries = [q.strip() for q in raw_q if isinstance(q, str) and q.strip()]

    # normalize sides: only dicts with "doc"
    raw_s = plan.get("sides", [])
    sides = [
        {"doc": s["doc"].strip()}
        for s in raw_s
        if isinstance(s, dict) and isinstance(s.get("doc"), str) and s["doc"].strip()
    ]

    # per-operation rules
    if op == "search":
        if not queries:
            queries = [user_query]
        queries = queries[:3]
        sides = []

    elif op == "compare":
        # queries may be []  →  whole-doc compare (valid!)
        queries = queries[:3]
        if len(sides) < 2:
            op = "search"          # can't compare without 2 sides
            sides = []
            if not queries:
                queries = [user_query]

    elif op == "summarize":
        # sides may be []  →  summarize all docs (valid!)
        queries = []

    else:  # chat, metadata, recall
        queries = []
        sides = []

    return {"operation": op, "queries": queries, "sides": sides}