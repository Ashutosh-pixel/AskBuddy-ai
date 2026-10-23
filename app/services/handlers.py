
import uuid

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.prompts.system_prompt import CHAT_PROMPT, RECALL_PROMPT

load_dotenv()

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
    )

async def handle_chat(user_query: str, history: list[dict]):

    response = await client.chat.completions.create(
        model="gemma4:e2b",
        messages=[
            {"role": "system", "content": CHAT_PROMPT},
            *history[-4:],
            {"role": "user", "content": user_query}
        ],
    )

    return {"answer": response.choices[0].message.content, "sources": []}

async def handle_recall(user_query: str, history: list[dict]):
    if not history:
        return {"answer": "We haven't discussed anything yet.", "sources": []}

    response = await client.chat.completions.create(
        model="gemma4:e2b",
        messages=[
            {"role": "system", "content": RECALL_PROMPT},
            *history[-4:],
            {"role": "user", "content": user_query}
        ],
    )

    return {"answer": response.choices[0].message.content, "sources": []}

async def handle_search(plan:dict, user_query: str, history: list[dict], conversation_id: uuid.UUID):
    # Implement the search handling logic here
    # This is a placeholder for the actual implementation
    return {"answer": "Search functionality is not yet implemented.", "sources": []}