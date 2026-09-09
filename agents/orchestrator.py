import llm
from agents.email_agent import EmailAgent
from agents.file_agent import FileAgent
from agents.schedule_agent import ScheduleAgent
from agents.study_agent import StudyAgent
from agents.quant_agent import QuantAgent
from agents.developer_agent import DeveloperAgent
from mission_store import MissionStore


class Orchestrator:
    """
    Routes a user message to the right specialist agent(s).
    Simple rule-based routing first (fast, free, predictable);
    falls back to asking the LLM to pick if nothing matches.
    """

    def __init__(self):
        self.store = MissionStore()
        self.agents = {
            "email": EmailAgent(),
            "file": FileAgent(),
            "schedule": ScheduleAgent(),
            "study": StudyAgent(self.store),
            "quant": QuantAgent(self.store),
            "developer": DeveloperAgent(self.store),
        }

    def get_status(self):
        return [
            {
                "key": key,
                "name": agent.name,
                "description": agent.description,
                "status": agent.status,
                "log": agent.log[-10:],
            }
            for key, agent in self.agents.items()
        ]

    def route(self, text: str) -> dict:
        candidates = self._enhancement_route(text)
        if not candidates:
            candidates = [key for key, agent in self.agents.items() if agent.can_handle(text)]

        if not candidates:
            candidates = [self._llm_pick(text)]

        results = []
        for key in candidates:
            agent = self.agents.get(key)
            if not agent:
                continue
            reply = agent.run(text)
            results.append({"agent": agent.name, "reply": reply, "status": "completed"})

        if not results:
            # generic fallback: just answer directly
            reply = llm.chat([{"role": "user", "content": text}])
            results.append({"agent": "General", "reply": reply, "status": "completed"})

        for result in results:
            self.store.record_command(text, result["agent"], result["reply"])
            self.store.add_activity(result["agent"], result["reply"].splitlines()[0][:120])

        if len(results) > 1:
            for index, result in enumerate(results[:-1]):
                self.store.add_handoff(None, result["agent"], results[index + 1]["agent"], result["reply"][:500])

        return {"task": text, "results": results}

    def dispatch_to(self, agent_key: str, text: str, history=None) -> dict | None:
        """Send a Worker Mode request to one explicitly selected specialist.

        This deliberately bypasses keyword and LLM routing used by Mission Control.
        """
        agent = self.agents.get(agent_key)
        if not agent:
            return None
        reply = agent.run(text, history=history)
        self.store.record_command(text, agent.name, reply)
        self.store.add_activity(agent.name, reply.splitlines()[0][:120] if reply else "Completed direct workspace request")
        return {"agent": agent.name, "reply": reply, "status": "completed"}

    def _enhancement_route(self, text: str):
        lowered = text.lower()
        enhancement_words = ("upgrade", "improve", "enhance", "add", "give", "make")
        target_phrases = ("email agent", "quant agent", "study agent", "developer agent")
        if any(word in lowered for word in enhancement_words) and any(phrase in lowered for phrase in target_phrases):
            return ["developer"]
        return []

    def _llm_pick(self, text: str) -> str:
        options = ", ".join(self.agents.keys())
        reply = llm.chat(
            [{"role": "user", "content": text}],
            system=(
                f"Pick exactly one of these agent keys that best fits the user's "
                f"request: {options}. Reply with ONLY the key, nothing else."
            ),
            max_tokens=10,
        )
        cleaned = reply.strip().lower()
        return cleaned if cleaned in self.agents else "file"
