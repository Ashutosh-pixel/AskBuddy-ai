from uuid import UUID

from fastapi import Request

from app.services.handlers import handle_chat, handle_recall, handle_search
from app.services.queryIntension_service import route
from sqlalchemy.ext.asyncio import AsyncSession


async def handle(request: Request, user_query:str, top_k: int, chat_history:list[dict], conversation_id:UUID, db:AsyncSession):
    plan = await route(user_query, chat_history)
    op = plan["operation"]
    print("op", plan)

    if op == "chat":
        return await handle_chat(user_query, chat_history)

    if op == "recall":
        return await handle_recall(user_query, chat_history)

    if op == "search":
        return await handle_search(request, user_query=user_query, queries=plan["queries"], top_k=top_k, chat_history=chat_history[-4:], conversation_id=conversation_id, db=db)

    return {"operation": plan["operation"], "queries": plan["queries"], "sides": plan["sides"]}