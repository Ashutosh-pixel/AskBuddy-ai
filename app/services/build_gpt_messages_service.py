# from app.utils.config import prompts

def build_get_messages(history):

    messages = [
        # {
        #     "role": "system",
        #     "content": prompts["system"]
        # }
    ]

    for message in history:
        messages.append({
            "role": message.role.value,
            "content": message.content
        })

    return messages
