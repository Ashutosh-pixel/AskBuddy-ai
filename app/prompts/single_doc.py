def singleDocPrompt(doc_name: str, context_text: list[str], query: str):
    return f"""You are an assistant answering questions strictly from the provided context.
    
    DOCUMENT SOURCE: {doc_name}

    CONTEXT:
    {context_text}

    USER QUESTION:
    {query}

    INSTRUCTIONS:
    Answer the question using ONLY the provided document context above. Do not combine details from outside files.
    """