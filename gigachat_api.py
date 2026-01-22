import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from analysis_api_base import AnalysisAPIBase
from langchain_client import build_chat_model
from langchain_utils import to_langchain_messages


class GigaChatAPI(AnalysisAPIBase):
    def __init__(self, model_name: str = "GigaChat"):
        """Инициализирует доступ к GigaChat и базовую логику анализа."""
        if load_dotenv is not None:
            load_dotenv()
        self.base_url = os.getenv(
            "GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        )
        self.api_token = os.getenv("GIGACHAT_API_TOKEN") or os.getenv("GIGACHAT_TOKEN")
        if not self.api_token:
            raise RuntimeError(
                "Не задан токен GigaChat. Установите GIGACHAT_API_TOKEN или GIGACHAT_TOKEN."
            )
        super().__init__(model_name)
        # Use OpenAI-compatible endpoint via LangChain.
        self.llm = build_chat_model(
            model_name=self.model_name, api_key=self.api_token, base_url=self.base_url
        )

    def call_model_raw(self, messages: list[dict]) -> str:
        """Отправляет сообщения в GigaChat и возвращает текст ответа."""
        try:
            response = self.llm.invoke(to_langchain_messages(messages))
        except Exception as e:
            return f"ERROR: Ошибка запроса к GigaChat - {e}"
        try:
            content = response.content.strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ GigaChat - {e}"
        return content
