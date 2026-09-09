import os
import re
import sqlite3
from datetime import datetime

import config
from agents.base import BaseAgent


class ScheduleAgent(BaseAgent):
    name = "Schedule Agent"
    description = "Tracks events, reminders and to-dos in a local database"

    KEYWORDS = ["schedule", "remind", "reminder", "calendar", "appointment",
                "meeting", "todo", "to-do", "event"]

    def __init__(self):
        super().__init__()
        os.makedirs(os.path.dirname(config.SCHEDULE_DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(config.SCHEDULE_DB_PATH)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                when_text TEXT,
                created_at TEXT
            )"""
        )
        conn.commit()
        conn.close()

    def can_handle(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.KEYWORDS)

    def handle(self, text: str) -> str:
        t = text.lower()

        if "list" in t or "what" in t or "show" in t:
            return self._list_events()
        if "delete" in t or "remove" in t or "cancel" in t:
            return self._delete_event(text)
        return self._add_event(text)

    def _add_event(self, text: str) -> str:
        when_match = re.search(
            r"(tomorrow|today|next \w+|on \w+|at \d{1,2}(:\d{2})?\s?(am|pm)?)",
            text.lower(),
        )
        when_text = when_match.group(0) if when_match else "unspecified time"

        conn = sqlite3.connect(config.SCHEDULE_DB_PATH)
        conn.execute(
            "INSERT INTO events (title, when_text, created_at) VALUES (?, ?, ?)",
            (text, when_text, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return f"Added: \"{text}\" (parsed time: {when_text})"

    def _list_events(self) -> str:
        conn = sqlite3.connect(config.SCHEDULE_DB_PATH)
        rows = conn.execute("SELECT id, title, when_text FROM events ORDER BY id DESC LIMIT 20").fetchall()
        conn.close()
        if not rows:
            return "No events scheduled yet."
        lines = [f"[{r[0]}] {r[1]} ({r[2]})" for r in rows]
        return "Upcoming/logged items:\n" + "\n".join(lines)

    def _delete_event(self, text: str) -> str:
        id_match = re.search(r"\d+", text)
        if not id_match:
            return "Tell me the event ID to delete (see 'list events' for IDs)."
        event_id = int(id_match.group(0))
        conn = sqlite3.connect(config.SCHEDULE_DB_PATH)
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        return f"Deleted event {event_id}."
