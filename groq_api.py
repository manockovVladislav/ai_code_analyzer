import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from analysis_api_base import AnalysisAPIBase
from langchain_client import build_chat_model
from langchain_utils import to_langchain_messages


class GroqAPI(AnalysisAPIBase):
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        """Инициализирует доступ к Groq (OpenAI-compatible API)."""
        if load_dotenv is not None:
            load_dotenv()
        self.base_url = os.getenv(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"
        )
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("Не задан ключ Groq. Установите GROQ_API_KEY.")
        super().__init__(model_name)
        # Use OpenAI-compatible endpoint via LangChain.
        self.llm = build_chat_model(
            model_name=self.model_name, api_key=self.api_key, base_url=self.base_url
        )

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в Groq и возвращает текст ответа."""
        try:
            response = await self.llm.ainvoke(to_langchain_messages(messages))
        except Exception as e:
            return f"ERROR: Ошибка запроса к Groq - {e}"
        try:
            content = response.content.strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ Groq - {e}"
        return content
