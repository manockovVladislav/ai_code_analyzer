import os
import asyncio
from model_api import ModelAPI
from project_loader import ProjectLoader
import reporter


class Agent:
    def __init__(self, model=None):
        """Создает агента и привязывает модель анализа."""
        self.model = model or ModelAPI()

    async def run_from_git(self, git_url: str, output_file: str = "analysis_report.md"):
        """Клонирует проект, анализирует файлы и сохраняет итоговый отчет."""
        loader = ProjectLoader()
        path = loader.clone_project(git_url)
        try:
            files = self._collect_files(path)
            print(f"[agent] Файлов для анализа: {len(files)}")
            plan_text = await self.model.get_plan(files)
            if plan_text:
                print("[agent] План анализа:")
                print(plan_text)
            analysis_results = {}
            action_log = []
            for file_path in files:
                print(f"[agent] Анализ файла: {file_path}")
                steps, result = await self._run_file_actions(file_path)
                analysis_results[file_path] = result
                action_log.extend(steps)
            reflection = await self.model.reflect(plan_text or "", action_log)
            report_md = reporter.generate_report(analysis_results, reflection=reflection)
            reporter.save_report(report_md, output_file)
            reporter.print_report_console(report_md)
            print(f"\nОтчет сохранен в файл: {output_file}")
        finally:
            loader.cleanup()

    async def run_from_path(self, local_path: str, output_file: str = "analysis_report.md"):
        """Анализирует локальный проект, уже размещенный в sandbox."""
        loader = ProjectLoader()
        path = loader.use_local_project(local_path)
        try:
            files = self._collect_files(path)
            print(f"[agent] Файлов для анализа: {len(files)}")
            plan_text = await self.model.get_plan(files)
            if plan_text:
                print("[agent] План анализа:")
                print(plan_text)
            analysis_results = {}
            action_log = []
            for file_path in files:
                print(f"[agent] Анализ файла: {file_path}")
                steps, result = await self._run_file_actions(file_path)
                analysis_results[file_path] = result
                action_log.extend(steps)
            reflection = await self.model.reflect(plan_text or "", action_log)
            report_md = reporter.generate_report(analysis_results, reflection=reflection)
            reporter.save_report(report_md, output_file)
            reporter.print_report_console(report_md)
            print(f"\nОтчет сохранен в файл: {output_file}")
        finally:
            # Не очищаем локальный путь, только при явном клоне
            pass

    async def _analyze_file(self, file_path: str):
        """Считывает файл и отправляет код в модель для анализа."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                code = file.read()
        except Exception as e:
            return file_path, f"ERROR: Не удалось прочитать файл ({e})"
        result = await self.model.analyze_code(file_path, code)
        return file_path, result

    def _collect_files(self, root_path: str) -> list[str]:
        """Собирает поддерживаемые файлы в проекте."""
        files = []
        for root, _, names in os.walk(root_path):
            for name in names:
                if name.endswith((".py", ".cpp", ".cc", ".cxx", ".hpp", ".h", ".java", ".sql")):
                    files.append(os.path.join(root, name))
        return sorted(files)

    async def _run_file_actions(self, file_path: str) -> tuple[list[str], str]:
        """Выполняет динамическую цепочку действий для файла."""
        steps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                code = file.read()
        except Exception as e:
            error_text = f"ERROR: Не удалось прочитать файл ({e})"
            print(f"[agent] Ошибка чтения: {file_path}")
            return [f"{file_path}: read_failed"], error_text
        steps.append(f"{file_path}: primary_analysis")
        print("[agent] Шаг: primary_analysis")
        result = await self.model.analyze_code(file_path, code)
        if self._needs_deeper_check(result):
            steps.append(f"{file_path}: deep_dive")
            print("[agent] Шаг: deep_dive (уточнение)")
            focus = "Уточни причины, последствия и возможные исправления."
            result = await self.model.analyze_code(file_path, code, focus_hint=focus)
        return steps, result

    def _needs_deeper_check(self, result: str) -> bool:
        """Решает, нужен ли повторный анализ по результату."""
        if not result:
            return False
        lowered = result.lower()
        triggers = ["ошибка", "уязв", "critical", "race", "инъекц", "overflow"]
        return any(token in lowered for token in triggers)
