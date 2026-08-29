import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

async def RAG_llm(context:str, question:str):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                            You are a helpful assistant.

                            Answer the user's question using only the provided context.

                            "If you don't have enough context, ask the user to upload a document so you can answer their question."

                            Context:
                            {context}

                            Question:
                            {question}

                            Answer:
                            """
            },
            {
                "role": "user",
                "content": context
            }
        ],
        model="openai/gpt-oss-20b",
    )

    return chat_completion.choices[0].message.content
