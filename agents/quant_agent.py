import re

from agents.base import BaseAgent
from mission_store import MissionStore


class QuantAgent(BaseAgent):
    name = "Quant Agent"
    description = "Organizes quantitative finance research and modeling missions"
    KEYWORDS = ["quant", "black-scholes", "black scholes", "monte carlo", "dcf", "capm", "financial model", "quantitative finance"]

    def __init__(self, store=None):
        super().__init__()
        self.store = store or MissionStore()

    def can_handle(self, text):
        lowered = text.lower()
        return any(keyword in lowered for keyword in self.KEYWORDS)

    def handle(self, text):
        lowered = text.lower()
        if "show" in lowered or "what" in lowered or "active" in lowered:
            missions = self.store.list_missions(category="Quant Finance")
            if not missions:
                return "No active quant missions are stored."
            return "Active quant missions:\n" + "\n".join(f"[{m['id']}] {m['title']} ({m['status']})" for m in missions if m["status"] != "completed")
        title = re.sub(r"^(create a mission to|create|work on|improve|build)\s*", "", text, flags=re.I).strip(" .")
        title = title or "Quant finance workflow"
        mission = self.store.create_mission(title, category="Quant Finance", priority="medium", estimated_minutes=90, project_importance=3, importance=2)
        self.store.add_activity(self.name, f"Created quant mission: {title}")
        return f"Quant mission created: [{mission['id']}] {title}. No market prediction was made."
