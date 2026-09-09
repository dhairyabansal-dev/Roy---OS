"""
Base class for every agent. Each specialist agent just needs to:
  1. set `name` and `description`
  2. implement `can_handle(text)` -> bool
  3. implement `handle(text)` -> str (the result/reply)
"""

import time


class BaseAgent:
    name = "base"
    description = "Base agent"

    def __init__(self):
        self.status = "idle"
        self.last_run = None
        self.log = []

    def can_handle(self, text: str) -> bool:
        raise NotImplementedError

    def handle(self, text: str) -> str:
        raise NotImplementedError

    def run(self, text: str, history=None) -> str:
        """Run an agent request, optionally with direct-workspace context."""
        self.status = "working"
        self._add_log(f"Task received: {text[:80]}")
        start = time.time()
        try:
            result = self.handle_with_history(text, history or [])
            self._add_log(f"Done in {time.time() - start:.1f}s")
            return result
        except Exception as e:
            self._add_log(f"Error: {e}")
            return f"[{self.name}] Error while handling task: {e}"
        finally:
            self.status = "idle"
            self.last_run = time.time()

    def handle_with_history(self, text: str, history: list[dict]) -> str:
        """Specialists can override this without changing the established handle contract."""
        return self.handle(text)

    def _add_log(self, message: str):
        self.log.append({"time": time.time(), "message": message})
        self.log = self.log[-50:]  # keep last 50 entries
