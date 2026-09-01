import os

from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

async def stream_llm(messages):
    stream = await client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        stream=True
    )

    async for event in stream:
        chunk = event.choices[0].delta.content

        if chunk:
            yield chunk
