"""Deterministic, project-scoped tools used by approved development missions."""

import os
import subprocess
import sys
from pathlib import Path


PROTECTED_NAMES = {
    ".env", ".env.local", ".env.production", "credentials.json",
    "secrets.json", "config.py", "id_rsa", "id_rsa.pub",
}
PROTECTED_PARTS = ("secret", "credential", "private_key", "api_key", "token")
ALLOWED_SUFFIXES = {".py", ".js", ".css", ".html", ".md", ".json", ".txt"}


class DevelopmentToolError(Exception):
    """Raised when a requested development operation is unsafe or invalid."""


class DevelopmentTools:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root or Path(__file__).resolve().parent).resolve()

    def _safe_path(self, relative_path):
        candidate = (self.project_root / relative_path).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise DevelopmentToolError("Path is outside the Agent Bay project root.") from exc
        if self._is_protected(candidate):
            raise DevelopmentToolError("Protected files cannot be exposed or modified.")
        if candidate.suffix.lower() not in ALLOWED_SUFFIXES:
            raise DevelopmentToolError("File type is not allowed for development edits.")
        return candidate

    @staticmethod
    def _is_protected(path):
        names = {part.lower() for part in path.parts}
        filename = path.name.lower()
        return filename in PROTECTED_NAMES or any(part in filename for part in PROTECTED_PARTS) or ".git" in names

    def read_file(self, relative_path):
        path = self._safe_path(relative_path)
        if not path.is_file():
            raise DevelopmentToolError("File does not exist.")
        return path.read_text(encoding="utf-8")

    def create_file(self, relative_path, content):
        path = self._safe_path(relative_path)
        if path.exists():
            raise DevelopmentToolError("Create refused because the file already exists.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return str(path.relative_to(self.project_root))

    def modify_file(self, relative_path, find, replace, expected_count=1):
        path = self._safe_path(relative_path)
        if not path.is_file():
            raise DevelopmentToolError("File does not exist.")
        content = path.read_text(encoding="utf-8")
        count = content.count(find)
        if count != expected_count:
            raise DevelopmentToolError(f"Expected {expected_count} exact match(es), found {count}.")
        path.write_text(content.replace(find, replace), encoding="utf-8", newline="\n")
        return str(path.relative_to(self.project_root))

    def apply_changes(self, changes):
        if not isinstance(changes, list) or not changes:
            raise DevelopmentToolError("At least one approved structured change is required.")
        modified, created = [], []
        for change in changes:
            operation = change.get("operation")
            path = change.get("path")
            if operation == "create":
                created.append(self.create_file(path, change.get("content", "")))
            elif operation == "modify":
                modified.append(self.modify_file(
                    path, change.get("find", ""), change.get("replace", ""),
                    int(change.get("expected_count", 1)),
                ))
            else:
                raise DevelopmentToolError("Only create and modify operations are supported.")
        return {"files_modified": modified, "files_created": created}

    def validate(self, files):
        """Run only fixed, project-local validation commands for changed files."""
        results = []
        for relative_path in files:
            path = self._safe_path(relative_path)
            if path.suffix.lower() == ".py":
                command = [sys.executable, "-m", "py_compile", str(path)]
            elif path.suffix.lower() == ".js":
                command = ["node", "--check", str(path)]
            else:
                continue
            try:
                completed = subprocess.run(
                    command, cwd=self.project_root, capture_output=True, text=True,
                    timeout=30, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                results.append({"file": relative_path, "passed": False, "summary": str(exc)})
                continue
            summary = (completed.stderr or completed.stdout or "passed").strip().splitlines()[-1]
            results.append({"file": relative_path, "passed": completed.returncode == 0, "summary": summary[:300]})
        return results
