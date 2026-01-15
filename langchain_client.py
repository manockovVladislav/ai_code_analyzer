import os

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


def _normalize_base_url(base_url: str | None) -> str | None:
    """Strip OpenAI chat-completions suffix for LangChain base_url."""
    if not base_url:
        return None
    suffix = "/chat/completions"
    if base_url.endswith(suffix):
        return base_url[: -len(suffix)]
    return base_url


def build_chat_model(model_name: str, api_key: str, base_url: str | None) -> "ChatOpenAI":
    """Create a LangChain chat model with OpenAI-compatible settings."""
    if ChatOpenAI is None:
        raise RuntimeError(
            "LangChain is not installed. Install langchain-openai and langchain-core."
        )
    # Keep defaults explicit to make provider overrides predictable.
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=_normalize_base_url(base_url or os.getenv("OPENAI_BASE_URL")),
        temperature=0,
        max_retries=2,
    )
