import asyncio
import json
import os
import urllib.request

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from analysis_api_base import AnalysisAPIBase


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

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в Groq и возвращает текст ответа."""
        payload = {"model": self.model_name, "messages": messages, "temperature": 0}
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        request = urllib.request.Request(self.base_url, data=data, headers=headers)

        try:
            response = await asyncio.to_thread(urllib.request.urlopen, request)
            body = response.read().decode("utf-8")
        except Exception as e:
            return f"ERROR: Ошибка запроса к Groq - {e}"
        try:
            data = json.loads(body)
            content = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"ERROR: Некорректный ответ Groq - {e}"
        return content
