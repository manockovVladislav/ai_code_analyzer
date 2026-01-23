import os

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


def _normalize_base_url(base_url: str | None) -> str | None:
    """Убирает суффикс chat-completions у base_url для LangChain."""
    if not base_url:
        return None
    suffix = "/chat/completions"
    if base_url.endswith(suffix):
        return base_url[: -len(suffix)]
    return base_url


def build_chat_model(model_name: str, api_key: str, base_url: str | None) -> "ChatOpenAI":
    """Создает LangChain chat-модель с OpenAI-совместимыми настройками."""
    if ChatOpenAI is None:
        raise RuntimeError(
            "LangChain is not installed. Install langchain-openai and langchain-core."
        )
    # Явно задаем дефолты, чтобы переопределения провайдера были предсказуемы.
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=_normalize_base_url(base_url or os.getenv("OPENAI_BASE_URL")),
        temperature=0,
        max_retries=2,
    )
