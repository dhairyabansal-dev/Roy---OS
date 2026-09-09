import json
import re
from pathlib import Path

from agents.base import BaseAgent
from agents.capability_registry import CAPABILITIES
from development_tools import DevelopmentToolError, DevelopmentTools
from mission_store import MissionStore


class DeveloperAgent(BaseAgent):
    name = "Developer Agent"
    description = "Inspects Agent Bay and plans safe enhancements for specialist agents"
    KEYWORDS = ["roy os", "agent bay", "developer", "development", "bug", "backlog", "feature", "python project", "hackathon", "blockchain", "code", "assignment", "mission", "priority", "continue", "upgrade", "improve", "enhance", "capability"]
    TARGET_PATTERNS = {
        "email": ("email agent", "email", "cold outreach", "cold email", "professional outreach"),
        "quant": ("quant agent", "quant", "calculus", "probability", "statistics", "black-scholes", "option pricing"),
        "study": ("study agent", "study", "acca", "financial accounting", "coursework", "degree material"),
        "developer": ("developer agent", "developer", "agent bay", "routing", "orchestrator"),
    }

    def __init__(self, store=None):
        super().__init__()
        self.store = store or MissionStore()
        self.tools = DevelopmentTools()

    def can_handle(self, text):
        lowered = text.lower()
        return any(keyword in lowered for keyword in self.KEYWORDS)

    def handle(self, text):
        lowered = text.lower()
        target = self._target_for(text)
        if target and self._is_enhancement_request(lowered):
            return self._enhancement_plan(text, target)
        if "capabilit" in lowered or "what can" in lowered:
            return self._capability_summary()
        if "show" in lowered or "active" in lowered:
            missions = self.store.list_missions(category="Programming") + self.store.list_missions(category="Hackathon")
            if not missions:
                return "No active development missions are stored."
            return "Active development missions:\n" + "\n".join(f"[{m['id']}] {m['title']} ({m['status']})" for m in missions if m["status"] != "completed")
        project_name = "ROY OS" if "roy os" in lowered else ("Agent Bay" if "agent bay" in lowered else "Development project")
        if "continue" in lowered or "next step" in lowered:
            projects = [p for p in self.store.projects() if project_name.lower() in p["name"].lower()]
            if projects:
                project = projects[0]
                return f"{project['name']}\nObjective: {project['objective'] or 'No objective recorded.'}\nNext action: {project['next_action'] or 'No next action recorded.'}"
        title = re.sub(r"^(add this |create a mission to |work on |continue )", "", text, flags=re.I).strip(" .")
        title = title or "Development task"
        mission = self.store.create_mission(title, category="Programming", priority="medium", estimated_minutes=90, project_importance=3, importance=2)
        self.store.add_activity(self.name, f"Created development mission: {title}")
        return f"Development mission created: [{mission['id']}] {title}."

    def _target_for(self, text):
        lowered = text.lower()
        matches = [key for key, patterns in self.TARGET_PATTERNS.items()
                   if any(pattern in lowered for pattern in patterns)]
        return matches[0] if len(matches) == 1 else ("developer" if "developer agent" in lowered else None)

    @staticmethod
    def _is_enhancement_request(lowered):
        return any(word in lowered for word in ("upgrade", "improve", "enhance", "add", "give", "make"))

    def _enhancement_plan(self, request, target):
        metadata = CAPABILITIES[target]
        source_path = Path(__file__).resolve().parents[1] / metadata["source"]
        inspection = self._inspect_source(source_path)
        capability = self._requested_capability(request, target)
        files = [metadata["source"]]
        if target == "study" and any(word in request.lower() for word in ("material", "knowledge", "document", "acca")):
            files.append("knowledge_store.py (new, only if material ingestion is approved)")
        plan_lines = [
            f"Target: {metadata['name']}",
            f"Requested capability: {capability}",
            "",
            "WHAT WILL CHANGE",
            f"- Extend {metadata['name']} around its existing responsibilities; preserve current routing and storage.",
            f"- Add focused support for {capability} with explicit validation and user-controlled side effects.",
            "",
            "FILES AFFECTED",
            *[f"- {path}" for path in files],
            "",
            "IMPLEMENTATION PLAN",
            "1. Reuse the current BaseAgent, MissionStore, and orchestrator interfaces.",
            f"2. Inspect {metadata['source']} before editing; current source is {inspection}.",
            "3. Add the smallest tool, prompt, or local knowledge component needed for the capability.",
            "4. Keep external actions approval-gated; drafts and calculations remain reviewable.",
            "5. Run syntax, import, routing, and capability-specific checks.",
            "",
            "RISKS",
            "- Runtime code changes require explicit approval and are not applied by this planning request.",
            "- Numerical answers should use deterministic calculations where available.",
            "",
            "VALIDATION",
            "- Python compile/import checks, targeted agent routing, and a request-specific smoke test.",
            "Approval required: say 'approve this enhancement' after reviewing the plan.",
        ]
        mission = self.store.create_mission(
            f"Enhance {metadata['name']}: {capability}",
            category="Programming",
            priority="high",
            estimated_minutes=90,
            project_importance=3,
            importance=3,
            objective=f"Implement approved enhancement requested: {request}",
            current_phase="queued",
            assigned_agent=self.name,
            target_agent=metadata["name"],
            enhancement_request=request,
            affected_files=json.dumps(files),
        )
        self.store.add_activity(self.name, f"Planned enhancement for {metadata['name']}: {capability}")
        return f"Enhancement plan recorded as mission [{mission['id']}].\n\n" + "\n".join(plan_lines)

    def analyze_mission(self, mission_id):
        mission = self.store.get_mission(mission_id)
        if not mission or mission["category"] != "Programming":
            return None
        if mission["status"] not in ("queued", "failed"):
            return mission
        self.store.update_workflow(mission_id, status="analyzing", progress=20, current_phase="analyzing")
        request = mission.get("enhancement_request") or mission.get("objective") or mission["title"]
        target_key = self._target_for(request) or self._target_key_from_name(mission.get("target_agent", ""))
        if not target_key:
            return self.store.update_workflow(
                mission_id, status="failed", progress=20, current_phase="failed",
                implementation_result="Could not identify a registered target agent.",
            )
        metadata = CAPABILITIES[target_key]
        source_path = Path(__file__).resolve().parents[1] / metadata["source"]
        inspection = self._inspect_source(source_path)
        files = [metadata["source"]]
        plan = (
            f"Target: {metadata['name']}\n"
            f"Requested capability: {request}\n"
            f"Inspection: {inspection}\n\n"
            "Implementation approach:\n"
            "- Apply only the approved structured edits for this mission.\n"
            "- Keep external actions approval-gated and reuse existing agent interfaces.\n"
            "- Validate every modified Python or JavaScript file with the fixed allowlist."
        )
        return self.store.update_workflow(
            mission_id, status="awaiting_approval", progress=40, current_phase="awaiting approval",
            target_agent=metadata["name"], enhancement_request=request, plan=plan,
            affected_files=json.dumps(files), implementation_result="Plan ready; awaiting user approval.",
        )

    def implement_mission(self, mission_id):
        mission = self.store.get_mission(mission_id)
        if not mission or mission["category"] != "Programming" or mission["status"] != "implementing":
            return None
        try:
            changes = json.loads(mission.get("implementation_changes") or "[]")
            result = self.tools.apply_changes(changes)
        except (ValueError, TypeError, DevelopmentToolError) as exc:
            return self.store.update_workflow(
                mission_id, status="failed", progress=60, current_phase="failed",
                implementation_result=f"Implementation refused: {exc}",
            )
        changed_files = result["files_modified"] + result["files_created"]
        mission = self.store.update_workflow(
            mission_id, status="validating", progress=85, current_phase="validating",
            files_modified=json.dumps(result["files_modified"]), files_created=json.dumps(result["files_created"]),
            implementation_result=f"Applied {len(changed_files)} approved file operation(s).",
        )
        return self.validate_mission(mission_id)

    def validate_mission(self, mission_id):
        mission = self.store.get_mission(mission_id)
        if not mission or mission["category"] != "Programming" or mission["status"] != "validating":
            return None
        files = json.loads(mission.get("files_modified") or "[]") + json.loads(mission.get("files_created") or "[]")
        results = self.tools.validate(files)
        passed = all(item["passed"] for item in results)
        summary = "\n".join(
            f"{'PASS' if item['passed'] else 'FAIL'} {item['file']}: {item['summary']}" for item in results
        ) or "No executable files changed; structural edit checks passed."
        return self.store.update_workflow(
            mission_id, status="completed" if passed else "failed", progress=100 if passed else 85,
            current_phase="completed" if passed else "failed", validation_result=summary,
        )

    @staticmethod
    def _target_key_from_name(name):
        lowered = name.lower()
        return next((key for key, value in CAPABILITIES.items() if value["name"].lower() == lowered), None)

    @staticmethod
    def _requested_capability(request, target):
        cleaned = re.sub(r"^(developer agent[:,]?\s*)", "", request, flags=re.I).strip(" .")
        return cleaned or ", ".join(CAPABILITIES[target]["enhancement_examples"][:2])

    @staticmethod
    def _inspect_source(path):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            return f"inspection unavailable ({exc})"
        classes = [line.strip()[6:].split("(")[0] for line in lines if line.lstrip().startswith("class ")]
        methods = [line.strip().split("(")[0][4:] for line in lines if line.lstrip().startswith("def ")]
        return f"{len(lines)} lines; classes={', '.join(classes) or 'none'}; methods={', '.join(methods) or 'none'}"

    @staticmethod
    def _capability_summary():
        lines = ["Agent Bay capability registry:"]
        for key, metadata in CAPABILITIES.items():
            lines.append(f"- {metadata['name']} ({key}): {', '.join(metadata['capabilities'])}")
        return "\n".join(lines)
