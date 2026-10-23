
import os
import json

from dotenv import load_dotenv
from groq import AsyncGroq
from openai import AsyncOpenAI

from app.prompts.rewriter_prompt import REWRITER_PROMPT

load_dotenv()

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


async def query_formulate(
    history: list[dict],
    user_query: str
) -> dict:

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

    content = response.choices[0].message.content
    print(content)

    if not content:
        raise ValueError("The model returned an empty response")
    
    return content