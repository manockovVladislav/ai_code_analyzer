import os
import shutil
import subprocess
import tempfile


class ProjectLoader:
    def __init__(self):
        """Готовит загрузчик для клонирования проекта во временную папку."""
        self.project_dir = None
        self.sandbox_dir = os.path.join(os.getcwd(), "sandbox")

    def clone_project(self, git_url: str) -> str:
        """Клонирует репозиторий и возвращает путь к временной директории."""
        os.makedirs(self.sandbox_dir, exist_ok=True)
        print(f"[loader] Клонирование репозитория: {git_url}")
        self.project_dir = tempfile.mkdtemp(prefix="project_", dir=self.sandbox_dir)
        print(f"[loader] Папка проекта: {self.project_dir}")
        subprocess.run(["git", "clone", git_url, self.project_dir], check=True)
        return self.project_dir

    def use_local_project(self, local_path: str) -> str:
        """Использует локальный путь проекта без клонирования."""
        abs_path = os.path.abspath(local_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Локальный путь не найден: {abs_path}")
        self.project_dir = abs_path
        print(f"[loader] Используем локальный проект: {self.project_dir}")
        return self.project_dir

    def cleanup(self):
        """Удаляет временную директорию проекта, если она была создана."""
        if self.project_dir and os.path.exists(self.project_dir):
            print(f"[loader] Очистка временной папки: {self.project_dir}")
            shutil.rmtree(self.project_dir)
