from app.services.handlers import handle_chat
from app.services.queryIntension_service import route


async def handle(user_query, history):
    plan = await route(user_query, history)
    op = plan["operation"]

    if op == "chat":
        return await handle_chat(user_query,history)

    if op == "recall":
        return await handle_chat(user_query,history)

    return {"operation": plan["operation"], "queries": plan["queries"], "sides": plan["sides"]}