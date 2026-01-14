import os
import asyncio

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import openai
from analysis_api_base import AnalysisAPIBase


class ModelAPI(AnalysisAPIBase):
    def __init__(self, model_name: str = "gpt-4"):
        """Инициализирует API модели, загружает ключ и память."""
        if load_dotenv is not None:
            load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise RuntimeError(
                "Не задан API-ключ для OpenAI. Установите переменную окружения OPENAI_API_KEY."
            )
        super().__init__(model_name)

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в модель и возвращает текст ответа."""
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                **{"model": self.model_name, "messages": messages, "temperature": 0},
            )
        except Exception as e:
            return f"ERROR: Ошибка запроса к модели - {e}"
        try:
            content = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ модели - {e}"
        return content
