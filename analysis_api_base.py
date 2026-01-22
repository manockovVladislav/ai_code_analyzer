import os
import re

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

    def _chunk_code(self, code: str, size: int = 800) -> list[str]:
        """Делит код на смысловые блоки (по абзацам) с ограничением размера."""
        if not code:
            return []
        paragraphs = [p for p in re.split(r"\n\s*\n", code) if p.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for para in paragraphs:
            para_len = len(para)
            if para_len > size:
                # Слишком большой абзац - режем по размеру
                if current:
                    chunks.append("\n\n".join(current))
                    current = []
                    current_len = 0
                for i in range(0, para_len, size):
                    chunks.append(para[i : i + size])
                continue
            if current_len + para_len + 2 > size and current:
                chunks.append("\n\n".join(current))
                current = [para]
                current_len = para_len
            else:
                current.append(para)
                current_len += para_len + 2
        if current:
            chunks.append("\n\n".join(current))
        return chunks

    def _extract_function_names(self, code: str, limit: int = 6) -> list[str]:
        """Пытается извлечь имена функций из кода."""
        if not code:
            return []
        patterns = [
            r"\bdef\s+([A-Za-z_]\w*)\s*\(",
            r"\b(?:[A-Za-z_][\w:<>\s*&]+\s+)+([A-Za-z_]\w*)\s*\(",
        ]
        names: list[str] = []
        for pattern in patterns:
            for match in re.findall(pattern, code):
                name = match if isinstance(match, str) else match[0]
                if name and name not in names:
                    names.append(name)
                if len(names) >= limit:
                    return names
        return names

    def call_model_raw(self, messages: list[dict]) -> str:
        """Отправляет сообщения в модель (без инструментов) и возвращает текст ответа."""
        raise NotImplementedError("call_model_raw должен быть реализован в подклассе")

    def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в модель и возвращает текст ответа."""
        return self.call_model_raw(messages)

    def get_plan(self, file_list: list[str]) -> str:
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
        return self.call_model_raw(messages)

    def update_plan(
        self, current_plan: str, action_log: list[str], remaining_files: list[str]
    ) -> str:
        """Обновляет план анализа с учетом уже выполненных шагов."""
        system_prompt = self._get_named_prompt(
            "plan_update.txt",
            "Обнови план анализа с учетом выполненных шагов и оставшихся файлов. "
            "Если план менять не нужно, повтори текущий. Выведи нумерованный список.",
        )
        remaining_names = ", ".join([os.path.basename(f) for f in remaining_files])
        log_text = "\n".join(action_log[-10:]) if action_log else ""
        user_prompt = (
            "Текущий план:\n"
            f"{current_plan}\n\n"
            "Последние действия:\n"
            f"{log_text}\n\n"
            f"Оставшиеся файлы: {remaining_names or 'нет'}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.call_model_raw(messages)

    def reflect(self, plan_text: str, action_log: list[str]) -> str:
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
        return self.call_model_raw(messages)

    def analyze_code(self, file_path: str, code: str, focus_hint: str | None = None) -> str:
        """Анализирует код файла с учетом языка, блоков и промежуточных выводов."""
        lang = self.detect_language(file_path)
        system_prompt = self._get_language_prompt(lang)
        chunks = self._chunk_code(code)
        self.memory.store_chunks(file_path, lang, chunks, kind="code")
        fence_lang = self._get_code_fence_lang(lang)
        summary_context = self.memory.get_recent_summaries(kind="file_summary", limit=3)
        summary_block = ""
        if summary_context:
            summary_block = "\n".join([f"- {item}" for item in summary_context if item])

        block_results: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            # Подмешиваем контекст из памяти, если блок короткий или есть дополнительный фокус.
            context_block = ""
            if len(chunk) < 400 or focus_hint:
                func_names = self._extract_function_names(chunk)
                if func_names:
                    query_text = " ".join(func_names)
                else:
                    query_text = f"{os.path.basename(file_path)} {lang}"
                context_chunks = self.memory.query(query_text, top_k=3, kind="code")
                if context_chunks:
                    context_block = "\n".join(
                        [f"- {item[:500]}" for item in context_chunks if item]
                    )
            user_prompt = (
                f"Файл: {os.path.basename(file_path)}\n"
                f"Язык: {lang}\n"
                f"Блок: {idx}/{len(chunks)}\n"
                "Код блока:\n"
                f"```{fence_lang}\n{chunk}\n```\n"
                "Найди баги, логические ошибки и уязвимости. "
                "Игнорируй стиль и форматирование."
            )
            if focus_hint:
                user_prompt += f"\nДополнительный фокус: {focus_hint}"
            if summary_block:
                user_prompt += "\nКраткие выводы по другим файлам:\n" + summary_block
            if context_block:
                user_prompt += "\nКонтекст из памяти (фрагменты кода):\n" + context_block
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            result = self.call_model(messages)
            block_results.append(result)
            self.memory.store_summary(
                scope=f"{file_path}:{idx}",
                text=result,
                kind="block_summary",
            )

        summary_prompt = self._get_named_prompt(
            "file_summary.txt",
            "Суммаризируй найденные проблемы по файлу, выдели критичные и повторяющиеся.",
        )
        summary_user = (
            f"Файл: {os.path.basename(file_path)}\n"
            f"Язык: {lang}\n"
            "Результаты анализа по блокам:\n"
            + "\n\n".join([f"- {text}" for text in block_results if text])
        )
        summary_messages = [
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": summary_user},
        ]
        summary_text = self.call_model_raw(summary_messages)
        self.memory.store_summary(scope=file_path, text=summary_text, kind="file_summary")

        report_parts = []
        for idx, result in enumerate(block_results, start=1):
            report_parts.append(f"#### Блок {idx}\n{result}")
        report_parts.append("#### Краткий вывод по файлу\n" + summary_text)
        return "\n\n".join(report_parts)

    def summarize_project(self, file_summaries: list[dict]) -> str:
        """Формирует общий вывод по проекту на основе выводов по файлам."""
        if not file_summaries:
            return ""
        system_prompt = self._get_named_prompt(
            "project_summary.txt",
            "Сформируй общий вывод по проекту, выдели критичные риски и повторяющиеся проблемы.",
        )
        items = []
        for item in file_summaries:
            scope = item.get("scope", "")
            text = item.get("text", "")
            if text:
                items.append(f"- {os.path.basename(scope)}: {text}")
        user_prompt = "Краткие выводы по файлам:\n" + "\n".join(items)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        summary = self.call_model_raw(messages)
        self.memory.store_summary(scope="project", text=summary, kind="project_summary")
        return summary
