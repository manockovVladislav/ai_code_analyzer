import argparse
import importlib.util
from pathlib import Path

from gigachat_api import GigaChatAPI
from koboldcpp_api import KoboldCppAPI
from local_model_api import LocalModelAPI


def _load_agent_class():
    """Загружает Agent из agent.py, обходя конфликт с пакетом agent/."""
    agent_path = Path(__file__).with_name("agent.py")
    spec = importlib.util.spec_from_file_location("agent_module", agent_path)
    if spec is None or spec.loader is None:
        raise ImportError("Не удалось загрузить module agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Agent


def main():
    """Парсит аргументы и запускает анализ репозитория."""
    parser = argparse.ArgumentParser(description="AI-Agent: анализ кода из Git-репозитория")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="URL Git-репозитория или локальный путь (по умолчанию ./sandbox)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="analysis_report.md",
        help="Путь для сохранения Markdown-отчета",
    )
    parser.add_argument(
        "--provider",
        choices=["gigachat", "local", "kobold"],
        default="kobold",
        help="Провайдер LLM (gigachat, local, kobold)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Имя модели провайдера (например, gpt-4 или GigaChat)",
    )
    args = parser.parse_args()
    Agent = _load_agent_class()
    if args.provider == "gigachat":
        model = GigaChatAPI(model_name=args.model or "GigaChat")
    elif args.provider == "kobold":
        model = KoboldCppAPI(model_name=args.model or "phi")
    else:
        model = LocalModelAPI(model_path=args.model)
    agent = Agent(model=model)
    source = args.source or "sandbox"
    if source.startswith("http://") or source.startswith("https://"):
        agent.run_from_git(source, output_file=args.output)
    else:
        agent.run_from_path(source, output_file=args.output)


if __name__ == "__main__":
    main()
