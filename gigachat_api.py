import asyncio
import json
import os
import urllib.request

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from analysis_api_base import AnalysisAPIBase


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

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в GigaChat и возвращает текст ответа."""
        payload = {"model": self.model_name, "messages": messages, "temperature": 0}
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        request = urllib.request.Request(self.base_url, data=data, headers=headers)

        try:
            response = await asyncio.to_thread(urllib.request.urlopen, request)
            body = response.read().decode("utf-8")
        except Exception as e:
            return f"ERROR: Ошибка запроса к GigaChat - {e}"
        try:
            data = json.loads(body)
            content = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ GigaChat - {e}"
        return content
