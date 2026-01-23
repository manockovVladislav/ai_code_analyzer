import os
import subprocess
from datetime import datetime


class AgentSandbox:
    """Runs small Python experiments in a local sandbox folder with a timeout."""

    def __init__(self, root_dir: str | None = None, timeout_sec: int = 60):
        self.root_dir = root_dir or os.path.join(os.path.dirname(__file__), "agent_sandbox")
        self.timeout_sec = timeout_sec
        os.makedirs(self.root_dir, exist_ok=True)

    def _build_script(self, user_code: str) -> str:
        header = (
            "import os\n"
            "import socket\n"
            "os.environ['NO_NETWORK'] = '1'\n"
            "def _blocked(*args, **kwargs):\n"
            "    raise RuntimeError('Network is disabled in agent_sandbox')\n"
            "socket.socket = _blocked\n"
            "socket.create_connection = _blocked\n"
            "try:\n"
            "    import urllib.request\n"
            "    urllib.request.urlopen = _blocked\n"
            "except Exception:\n"
            "    pass\n"
            "try:\n"
            "    import requests\n"
            "    requests.sessions.Session.request = _blocked\n"
            "except Exception:\n"
            "    pass\n"
            "\n"
        )
        return header + user_code

    def run(self, user_code: str, input_text: str | None = None) -> dict:
        """Runs code with a timeout and logs output to agent_sandbox/last_run.log."""
        script_path = os.path.join(self.root_dir, "last_run.py")
        log_path = os.path.join(self.root_dir, "last_run.log")
        full_code = self._build_script(user_code)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(full_code)

        env = os.environ.copy()
        env["PYTHONNOUSERSITE"] = "1"
        env["NO_NETWORK"] = "1"
        started = datetime.utcnow().isoformat() + "Z"
        try:
            result = subprocess.run(
                ["python3", "-I", script_path],
                input=input_text.encode("utf-8") if input_text is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout_sec,
                env=env,
                cwd=self.root_dir,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b"").decode("utf-8", errors="replace")
            output += "\nERROR: Sandbox timeout exceeded.\n"
            exit_code = 124

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"started: {started}\n")
            f.write(f"exit_code: {exit_code}\n")
            f.write(output)

        return {
            "exit_code": exit_code,
            "output": output,
            "script_path": script_path,
            "log_path": log_path,
        }
