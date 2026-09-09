import re

import llm
from agents.base import BaseAgent
from mission_store import MissionStore


class StudyAgent(BaseAgent):
    name = "Study Agent"
    description = "Builds focused study missions and tracks academic progress"
    KEYWORDS = ["study", "acca", "chapter", "subject", "topic", "exam", "academic", "class"]

    def __init__(self, store=None):
        super().__init__()
        self.store = store or MissionStore()

    def can_handle(self, text):
        lowered = text.lower()
        return any(keyword in lowered for keyword in self.KEYWORDS)

    def handle(self, text):
        lowered = text.lower()
        if "what should i study" in lowered or "study queue" in lowered:
            missions = self.store.list_missions(category="ACCA") + self.store.list_missions(category="University")
            active = [m for m in missions if m["status"] != "completed"]
            if not active:
                return "Study queue is empty. Name a subject or chapter to create the next mission."
            return "Study queue:\n" + "\n".join(f"[{m['id']}] {m['title']} ({m['priority']})" for m in active[:10])
        if "mark" in lowered and "complete" in lowered:
            match = re.search(r"\b(\d+)\b", text)
            if match:
                mission = self.store.complete_mission(int(match.group(1)))
                if mission:
                    self.store.add_activity(self.name, f"Completed study mission: {mission['title']}")
                    return f"Completed study mission: {mission['title']}"
            return "Give me the mission ID to mark complete."

        minutes = self._duration(text)
        title = re.sub(r"^(start studying|study|create a .* session for|prepare for)\s*", "", text, flags=re.I).strip(" .")
        title = title or "Focused study session"
        category = "ACCA" if any(word in lowered for word in ("acca", "accounting", "financial accounting")) else "University"
        mission = self.store.create_mission(title, category=category, priority="high", estimated_minutes=minutes, academic_relevance=3, importance=2)
        self.store.add_activity(self.name, f"Created {category} study mission: {title}")
        return f"Study mission created: [{mission['id']}] {title} ({minutes} minutes, {category})."

    def handle_with_history(self, text, history):
        """Answer learning questions conversationally while retaining the normal task workflow."""
        lowered = text.lower()
        task_intent = any(phrase in lowered for phrase in (
            "study ", "create", "prepare", "start", "mark", "study queue", "what should i study",
        ))
        if task_intent:
            return self.handle(text)
        context = [
            {"role": item["role"], "content": item["content"]}
            for item in history[-12:]
            if item.get("role") in ("user", "agent")
        ]
        context.append({"role": "user", "content": text})
        return llm.chat(
            context,
            system=(
                "You are the Study Agent in Agent Bay, an academic learning assistant. "
                "Give a clear, accurate, concise explanation suited to the user's question. "
                "Use the conversation context when it is relevant. Do not claim to have completed "
                "a study task unless one was actually created."
            ),
        )

    @staticmethod
    def _duration(text):
        match = re.search(r"(\d+)\s*(hour|hr|minute|min)s?", text.lower())
        if not match:
            return 60
        amount = int(match.group(1))
        return amount * 60 if match.group(2).startswith("h") else amount
