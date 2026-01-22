import os

try:
    import requests
except ImportError:
    requests = None

from analysis_api_base import AnalysisAPIBase


class KoboldCppAPI(AnalysisAPIBase):
    def __init__(
        self,
        base_url: str | None = None,
        model_name: str = "phi",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """Инициализирует OpenAI-совместимый HTTP API (например, KoboldCpp)."""
        if requests is None:
            raise RuntimeError("Не найдена зависимость requests. Установите requests.")
        resolved_base_url = (
            base_url
            or os.getenv("KOBOLD_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "http://127.0.0.1:5001"
        )
        super().__init__(model_name=model_name)
        self.base_url = resolved_base_url.rstrip("/")
        self.max_tokens = int(max_tokens or os.getenv("KOBOLD_MAX_TOKENS", "512"))
        self.temperature = float(temperature or os.getenv("KOBOLD_TEMPERATURE", "0.1"))
        self.timeout = int(os.getenv("KOBOLD_TIMEOUT", "600"))

    def _build_prompt(self, messages: list[dict]) -> str:
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"[{role}]\n{content}")
        return "\n\n".join(parts) + "\n\n[assistant]\n"

    def call_model_raw(self, messages: list[dict]) -> str:
        """Отправляет сообщения в KoboldCpp/OpenAI-compatible API и возвращает ответ."""
        chat_payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=chat_payload,
                timeout=self.timeout,
            )
        except Exception as exc:
            return f"ERROR: Ошибка HTTP-запроса - {exc}"
        if response.status_code == 200:
            try:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as exc:
                return f"ERROR: Некорректный ответ chat-completions - {exc}"

        prompt = self._build_prompt(messages)
        comp_payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        try:
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=comp_payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0].get("text", "").strip()
        except Exception as exc:
            return f"ERROR: Ошибка fallback completions - {exc}"
