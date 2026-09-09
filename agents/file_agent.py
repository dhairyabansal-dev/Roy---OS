import os
import re
import shutil

import config
import llm
from agents.base import BaseAgent


class FileAgent(BaseAgent):
    name = "File Agent"
    description = "Searches, summarizes, renames and organizes files"

    KEYWORDS = ["file", "folder", "document", "rename", "move", "organize",
                "downloads", "summarize", "pdf", "delete", "find"]

    def can_handle(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.KEYWORDS)

    def handle(self, text: str) -> str:
        t = text.lower()

        if "find" in t or "search" in t:
            return self._search(text)
        if "organize" in t or "clean" in t:
            return self._organize_summary()
        if "summarize" in t:
            return self._summarize_hint(text)

        # default: ask the LLM to explain what it *would* do, since actually
        # renaming/deleting things automatically is risky without confirmation
        reply = llm.chat(
            [{"role": "user", "content": text}],
            system=(
                "You are a file management assistant. The user wants help with "
                "files on their computer. Explain clearly and concisely what "
                "steps you would take. Do not claim you already did it."
            ),
        )
        return reply

    def _search(self, text: str) -> str:
        # naive keyword extraction: last quoted string or last word
        match = re.search(r'"([^"]+)"', text)
        term = match.group(1) if match else text.split()[-1]

        matches = []
        root = config.FILE_AGENT_ROOT
        for dirpath, _, filenames in os.walk(root):
            if len(matches) > 20:
                break
            for fname in filenames:
                if term.lower() in fname.lower():
                    matches.append(os.path.join(dirpath, fname))

        if not matches:
            return f"No files matching '{term}' found under {root}."
        listing = "\n".join(f"- {m}" for m in matches[:20])
        return f"Found {len(matches)} file(s) matching '{term}':\n{listing}"

    def _organize_summary(self) -> str:
        root = config.FILE_AGENT_ROOT
        downloads = os.path.join(root, "Downloads")
        if not os.path.isdir(downloads):
            return f"No Downloads folder found at {downloads}."

        by_ext = {}
        for fname in os.listdir(downloads):
            path = os.path.join(downloads, fname)
            if os.path.isfile(path):
                ext = os.path.splitext(fname)[1].lower() or "no_extension"
                by_ext.setdefault(ext, []).append(fname)

        lines = [f"{ext}: {len(files)} file(s)" for ext, files in by_ext.items()]
        return "Downloads folder breakdown (dry-run, nothing moved yet):\n" + "\n".join(lines) + \
               "\n\nSay 'move <ext> files into <folder>' to actually move a group."

    def _summarize_hint(self, text: str) -> str:
        return (
            "To summarize a document, upload it or give me its exact path, "
            "and I'll read and summarize it for you."
        )
