import os
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from analysis_api_base import AnalysisAPIBase
from langchain_client import build_chat_model
from langchain_utils import to_langchain_messages


class ModelAPI(AnalysisAPIBase):
    def __init__(self, model_name: str = "gpt-4"):
        """Инициализирует API модели, загружает ключ и память."""
        if load_dotenv is not None:
            load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Не задан API-ключ для OpenAI. Установите переменную окружения OPENAI_API_KEY."
            )
        super().__init__(model_name)
        # LangChain chat model handles retries and OpenAI-compatible calls.
        self.llm = build_chat_model(model_name=self.model_name, api_key=api_key, base_url=None)

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в модель и возвращает текст ответа."""
        try:
            response = await self.llm.ainvoke(to_langchain_messages(messages))
        except Exception as e:
            return f"ERROR: Ошибка запроса к модели - {e}"
        try:
            content = response.content.strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ модели - {e}"
        return content
