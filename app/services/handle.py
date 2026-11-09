from uuid import UUID

from fastapi import Request

from app.services.handlers import handle_chat, handle_compare, handle_metadata, handle_recall, handle_search
from app.services.queryIntension_service import route
from sqlalchemy.ext.asyncio import AsyncSession


async def dispatch(request: Request, user_query:str, top_k: int, chat_history:list[dict], conversation_id:UUID, db:AsyncSession):
    plan = await route(user_query, chat_history)
    op = plan["operation"]
    print("op", plan)

    if op == "chat":
        return await handle_chat(user_query, chat_history)

    if op == "recall":
        return await handle_recall(user_query, chat_history)

    if op == "search":
        return await handle_search(request, user_query=user_query, plan=plan, top_k=top_k, chat_history=chat_history[-4:], conversation_id=conversation_id, db=db)

    if op == "compare":
        return await handle_compare(request, db=db, conversation_id=conversation_id, plan=plan, user_query=user_query, chat_history=chat_history)

    if op == "metadata":
        return await handle_metadata(db=db, conversation_id=conversation_id, user_query=user_query)

    return {"operation": plan["operation"], "queries": plan["queries"], "sides": plan["sides"]}