import os

from memory import CodeMemory


class AnalysisAPIBase:
    """Базовая логика анализа: промпты, язык, чанки и память."""

    def __init__(self, model_name: str, prompt_dir: str | None = None, memory=None):
        """Инициализирует базовую часть анализа и память."""
        self.model_name = model_name
        self.prompt_dir = prompt_dir or os.path.join(os.path.dirname(__file__), "prompts")
        self.memory = memory or CodeMemory()

    def detect_language(self, file_path: str) -> str:
        """Определяет язык по расширению файла."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "Python",
            ".pyw": "Python",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".hpp": "C++",
            ".h": "C++",
            ".java": "Java",
            ".sql": "SQL",
        }
        return mapping.get(ext, "Generic")

    def _read_prompt_file(self, filename: str) -> str:
        """Читает файл промпта по имени, возвращает текст или пустую строку."""
        path = os.path.join(self.prompt_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    def _get_named_prompt(self, filename: str, fallback: str) -> str:
        """Возвращает промпт из файла или fallback-текст."""
        prompt = self._read_prompt_file(filename)
        return prompt or fallback

    def _get_language_prompt(self, lang: str) -> str:
        """Выбирает системный промпт для заданного языка."""
        mapping = {
            "Python": "python.txt",
            "C++": "cpp.txt",
            "Java": "java.txt",
            "SQL": "sql.txt",
            "Generic": "generic.txt",
        }
        filename = mapping.get(lang, "generic.txt")
        return self._get_named_prompt(
            filename,
            "Ты анализируешь код на наличие багов и логических ошибок. "
            "Игнорируй стиль и форматирование, интересуют только реальные проблемы.",
        )

    def _get_code_fence_lang(self, lang: str) -> str:
        """Возвращает метку языка для markdown code fence."""
        mapping = {
            "Python": "python",
            "C++": "cpp",
            "Java": "java",
            "SQL": "sql",
        }
        return mapping.get(lang, "")

    def _chunk_code(self, code: str, size: int = 500) -> list[str]:
        """Делит код на чанки фиксированного размера."""
        return [code[i : i + size] for i in range(0, len(code), size)]

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в модель и возвращает текст ответа."""
        raise NotImplementedError("call_model должен быть реализован в подклассе")

    async def get_plan(self, file_list: list[str]) -> str:
        """Строит план анализа на основе списка файлов."""
        system_prompt = self._get_named_prompt(
            "plan.txt",
            "Составь краткий план анализа для списка файлов. Выведи нумерованный список.",
        )
        file_names = ", ".join([os.path.basename(f) for f in file_list])
        user_prompt = f"Файлы проекта: {file_names}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.call_model(messages)

    async def reflect(self, plan_text: str, action_log: list[str]) -> str:
        """Оценивает результаты анализа и предлагает улучшения."""
        system_prompt = self._get_named_prompt(
            "reflect.txt",
            "Оцени результаты анализа и укажи, что можно улучшить.",
        )
        log_text = "\n".join(action_log)
        user_prompt = f"План:\n{plan_text}\n\nНаблюдения:\n{log_text}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.call_model(messages)

    async def analyze_code(self, file_path: str, code: str, focus_hint: str | None = None) -> str:
        """Анализирует код файла с учетом языка и памяти."""
        lang = self.detect_language(file_path)
        system_prompt = self._get_language_prompt(lang)
        chunks = self._chunk_code(code)
        self.memory.store_chunks(file_path, lang, chunks)
        fence_lang = self._get_code_fence_lang(lang)
        context_chunks = self.memory.query(os.path.basename(file_path), top_k=3)
        context_block = ""
        if context_chunks:
            context_block = "\n".join(
                [f"- {chunk[:500]}" for chunk in context_chunks if chunk]
            )
        user_prompt = (
            f"Файл: {os.path.basename(file_path)}\n"
            f"Язык: {lang}\n"
            "Код:\n"
            f"```{fence_lang}\n{code}\n```\n"
            "Найди баги, логические ошибки и уязвимости. "
            "Игнорируй стиль и форматирование."
        )
        if focus_hint:
            user_prompt += f"\nДополнительный фокус: {focus_hint}"
        if context_block:
            user_prompt += "\nКонтекст из памяти (фрагменты кода):\n" + context_block
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.call_model(messages)
