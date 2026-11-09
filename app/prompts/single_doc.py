def singleDocPrompt(doc_name: str, context_text: str, scope_label: str | None) -> str:
    scope_note = ""
    if scope_label:
        scope_note = (
            f"\nThe user scoped this query to: {scope_label}. "
            f"If the answer isn't in the provided context, say "
            f"the information is not available in {scope_label}."
        )

    return f"""You are an AI assistant answering questions strictly from the
    provided document context.

    DOCUMENT SOURCE:
    {doc_name}

    DOCUMENT CONTEXT:
    {context_text}

    INSTRUCTIONS:
    1. Answer factual questions strictly using the provided document context.
    2. Do not use information from the conversation history as a factual source.
    3. Do not combine information from other documents or external knowledge.
    4. If the question cannot be answered from the context, clearly say the
    information is not available in the provided document.
    5. Use the conversation history only to understand references ("it", "that",
    "the above") — not as a factual source.
    6. Be clear, concise, and natural. Avoid repeating the context verbatim.{scope_note}
    """