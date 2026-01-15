from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


def to_langchain_messages(messages: list[dict]) -> list:
    """Convert simple role/content dicts into LangChain message objects."""
    converted = []
    for item in messages:
        role = item.get("role", "")
        content = item.get("content", "")
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            # Default to human to avoid dropping unknown roles.
            converted.append(HumanMessage(content=content))
    return converted
