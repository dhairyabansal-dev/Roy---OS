"""Stop only the Agent Bay backend started by the local launcher."""

import os
import signal
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PID_PATH = ROOT / "data" / "agent_bay_server.pid"


def main():
    if not PID_PATH.exists():
        print("Agent Bay is not running (no launcher PID file found).")
        return 0
    try:
        pid = int(PID_PATH.read_text(encoding="ascii").strip())
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode not in (0, 128):
                raise OSError(result.stderr.strip() or result.stdout.strip())
        else:
            os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError) as error:
        print(f"Could not stop Agent Bay process: {error}")
        PID_PATH.unlink(missing_ok=True)
        return 1
    for _ in range(20):
        if os.name == "nt":
            probe = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            still_running = str(pid) in probe.stdout
        else:
            try:
                os.kill(pid, 0)
                still_running = True
            except OSError:
                still_running = False
        if not still_running:
            PID_PATH.unlink(missing_ok=True)
            print("Agent Bay stopped.")
            return 0
        time.sleep(0.25)
    print(f"Agent Bay process {pid} did not exit promptly. End it from Task Manager if needed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())