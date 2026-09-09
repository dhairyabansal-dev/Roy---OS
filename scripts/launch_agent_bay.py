"""Start Agent Bay and open its local dashboard on Windows."""

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config  # noqa: E402


def url_base():
    host = "127.0.0.1" if config.HOST in ("0.0.0.0", "::") else config.HOST
    return f"http://{host}:{config.PORT}"


def dashboard_ready():
    try:
        with urllib.request.urlopen(f"{url_base()}/api/status", timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ollama_ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            models = response.read().decode("utf-8")
            return config.OLLAMA_MODEL in models
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_ollama():
    if not config.USE_OLLAMA or ollama_ready():
        return True
    executable = shutil.which("ollama")
    if not executable:
        print("[!] Ollama is not installed or is not on PATH.")
        return False
    print("[>] Starting Ollama...")
    subprocess.Popen(
        [executable, "serve"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    for _ in range(20):
        if ollama_ready():
            return True
        time.sleep(1)
    print(f"[!] Ollama started, but model '{config.OLLAMA_MODEL}' is unavailable.")
    print(f"    Run: ollama pull {config.OLLAMA_MODEL}")
    return False


def python_executable():
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv311" / "Scripts" / "python.exe",
        ROOT / ".venv-1" / "Scripts" / "python.exe",
        ROOT / "venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists() and interpreter_ready(str(candidate)):
            return str(candidate)
    return sys.executable


def interpreter_ready(executable):
    try:
        result = subprocess.run(
            [executable, "-c", "import fastapi, uvicorn, qrcode, requests"],
            cwd=str(ROOT), capture_output=True, timeout=5, check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def start_backend():
    if dashboard_ready():
        print(f"[✓] Agent Bay is already running at {url_base()}")
        return True
    executable = python_executable()
    if executable == sys.executable:
        if (ROOT / ".venv").exists() or (ROOT / "venv").exists():
            print("[i] Project virtual environment is missing required packages; using the current Python interpreter.")
        else:
            print("[i] No project virtual environment found; using the current Python interpreter.")
    log_path = ROOT / "data" / "agent_bay_server.log"
    log_path.parent.mkdir(exist_ok=True)
    pid_path = ROOT / "data" / "agent_bay_server.pid"
    log_file = log_path.open("a", encoding="utf-8")
    print("[>] Starting Mission Control...")
    process = subprocess.Popen(
        [executable, str(ROOT / "main.py")],
        cwd=str(ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    log_file.close()
    pid_path.write_text(str(process.pid), encoding="ascii")
    for _ in range(30):
        if dashboard_ready():
            return True
        time.sleep(1)
    print(f"[!] Agent Bay did not become reachable. Inspect {log_path}")
    if process.poll() is None:
        process.terminate()
    pid_path.unlink(missing_ok=True)
    return False


def main():
    os.chdir(ROOT)
    print("AGENT BAY / LOCAL AI MISSION CONTROL")
    print(f"[✓] Installation: {ROOT}")
    print(f"[✓] Target: {url_base()}")
    if config.USE_OLLAMA and not start_ollama():
        print("[!] Continuing without a verified Ollama model; local LLM commands may fail.")
    if not start_backend():
        return 1
    print("[✓] SYSTEM ONLINE")
    webbrowser.open(url_base())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())