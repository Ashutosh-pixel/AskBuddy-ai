import os

from app.utils.config import prompts
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

async def ask_llm(question:str):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompts["system"],
            },
            {
                "role": "user", 
                "content": question
            },
        ],
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content
