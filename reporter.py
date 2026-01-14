import os


def generate_report(
    analysis_results: dict[str, str],
    summary: str | None = None,
    reflection: str | None = None,
) -> str:
    """Формирует содержимое отчета в формате Markdown на основе результатов анализа."""
    lines: list[str] = []
    # Заголовок отчета
    lines.append("# Отчет анализа кода")
    # Раздел с обнаруженными проблемами по файлам
    if analysis_results:
        lines.append("\n## Обнаруженные проблемы по файлам:\n")
        for file_path, analysis in analysis_results.items():
            file_name = os.path.basename(file_path)
            lines.append(f"### Файл: `{file_name}`")
            # Добавляем пустую строку перед списком проблем для корректного Markdown-форматирования
            if analysis and not analysis.startswith("\n"):
                lines.append("")
            # Если в анализе содержится отметка об ошибке, выделяем курсивом
            analysis_text = analysis.strip()
            if analysis_text.upper().startswith("ERROR"):
                analysis_text = f"*{analysis_text}*"
            lines.append(analysis_text)
            lines.append("")  # пустая строка после каждого файла
    # Раздел общий вывод/заключение, если есть
    if summary:
        lines.append("## Общий вывод\n")
        lines.append(summary.strip())
    if reflection:
        lines.append("## Рефлексия\n")
        lines.append(reflection.strip())
    # Объединяем все линии в один текст с переводами строк
    return "\n".join(lines)


def save_report(report_md: str, file_path: str):
    """Сохраняет отчет в указанный файл (в кодировке UTF-8)."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report_md)
    except Exception as e:
        print(f"Не удалось сохранить отчет в файл {file_path}: {e}")


def print_report_console(report_md: str):
    """Выводит отчет в консоль с подсветкой, если доступна библиотека rich."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        console.print(Markdown(report_md))
    except ImportError:
        # Если rich не установлен, выводим обычным текстом
        print(report_md)
