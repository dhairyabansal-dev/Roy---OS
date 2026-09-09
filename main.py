from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from io import BytesIO
import json
try:
   import qrcode
except ImportError:
    qrcode = None
from pydantic import BaseModel

import config
import network
from agents.capability_registry import describe_capabilities
from agents.orchestrator import Orchestrator

app = FastAPI(title="Local Agent Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()

history = []  # simple in-memory chat log for the dashboard


class TaskRequest(BaseModel):
    text: str


class AgentChatRequest(BaseModel):
    message: str


class MissionStatusRequest(BaseModel):
    status: str


class ProjectRequest(BaseModel):
    name: str
    description: str = ""
    objective: str = ""
    current_phase: str = ""
    technologies: str = ""
    agents_involved: str = ""
    status: str = "active"
    next_action: str = ""
    important_files: str = ""
    notes: str = ""


class SubtaskRequest(BaseModel):
    title: str
    position: int = 0


class SubtaskStatusRequest(BaseModel):
    status: str


class ImplementationApprovalRequest(BaseModel):
    approved_by: str = "user"
    changes: list[dict] = []


@app.get("/api/status")
def status():
    snapshot = orchestrator.store.snapshot()
    next_action = orchestrator.store.next_best_action()
    if next_action:
        next_action = {**next_action, "score": orchestrator.store.priority_analysis(next_action)["score"],
                       "priority_analysis": orchestrator.store.priority_analysis(next_action),
                       "subtasks": orchestrator.store.subtasks(next_action["id"])}
    for mission in snapshot["missions"]:
        mission["subtasks"] = orchestrator.store.subtasks(mission["id"])
    lan_addresses = network.private_ipv4_addresses()
    return {"agents": orchestrator.get_status(), "next_action": next_action,
            "system": {"online": True, "local_model": config.OLLAMA_MODEL if config.USE_OLLAMA else "fallback API",
                        "memory": "active", "lan_addresses": lan_addresses,
                        "mobile_url": network.mobile_access_url(config.PORT)}, **snapshot}


@app.get("/api/network")
def network_status():
    addresses = network.private_ipv4_addresses()
    return {"addresses": addresses, "mobile_url": network.mobile_access_url(config.PORT),
            "port": config.PORT, "lan_enabled": config.HOST in ("0.0.0.0", "::")}


@app.get("/api/network/qr")
def network_qr():
    url = network.mobile_access_url(config.PORT)
    if not url:
        return {"error": "No private LAN IPv4 address is available."}
    if qrcode is None:
        return {"error": "QR support is not installed. Run: python -m pip install -r requirements.txt"}
    image = qrcode.make(url)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    return Response(content=buffer.getvalue(), media_type="image/png",
                    headers={"Cache-Control": "no-store"})


@app.get("/api/history")
def get_history():
    return {"history": orchestrator.store.history()}


@app.get("/api/agents")
def get_agents():
    """Worker Mode directory data, without changing Mission Control status APIs."""
    agents = orchestrator.get_status()
    for agent in agents:
        _, messages = orchestrator.store.conversation_messages(agent["key"], limit=1)
        agent["conversation_message_count"] = len(orchestrator.store.conversation_messages(agent["key"], limit=100)[1])
        agent["last_message"] = messages[-1] if messages else None
        agent["active_task_count"] = len([
            mission for mission in orchestrator.store.list_missions(limit=100)
            if mission.get("assigned_agent") == agent["name"] and mission["status"] not in ("completed", "failed")
        ])
    return {"agents": agents}


@app.get("/api/agents/{agent_id}/chat")
def get_agent_chat(agent_id: str):
    if agent_id not in orchestrator.agents:
        return {"error": "Agent not found"}
    conversation, messages = orchestrator.store.conversation_messages(agent_id)
    return {"agent": orchestrator.get_status()[list(orchestrator.agents).index(agent_id)],
            "conversation": conversation, "messages": messages}


@app.post("/api/agents/{agent_id}/chat")
def agent_chat(agent_id: str, req: AgentChatRequest):
    if agent_id not in orchestrator.agents:
        return {"error": "Agent not found"}
    message = req.message.strip()
    if not message:
        return {"error": "Message cannot be empty"}
    _, history = orchestrator.store.conversation_messages(agent_id)
    user_message = orchestrator.store.add_conversation_message(agent_id, "user", message)
    result = orchestrator.dispatch_to(agent_id, message, history=history)
    if not result:
        return {"error": "Agent not found"}
    agent_message = orchestrator.store.add_conversation_message(agent_id, "agent", result["reply"])
    conversation, messages = orchestrator.store.conversation_messages(agent_id)
    return {"agent": result["agent"], "reply": result["reply"], "status": result["status"],
            "conversation": conversation, "user_message": user_message,
            "agent_message": agent_message, "messages": messages}


@app.get("/api/capabilities")
def capabilities():
    return {"capabilities": describe_capabilities()}


@app.get("/api/system/credentials")
def credential_status():
    return config.credential_presence()


@app.get("/api/briefing")
def briefing():
    snapshot = orchestrator.store.snapshot()
    active = sorted(snapshot["active_missions"], key=orchestrator.store.priority_score, reverse=True)
    next_action = active[0] if active else None
    briefing_lines = ["GOOD MORNING, ROY.", "", "SYSTEM STATUS", "All agents operational.", "",
                      "ACTIVE MISSIONS", f"{len(active)} missions currently active.", "",
                      "NEXT BEST ACTION", next_action["title"] if next_action else "No active missions."]
    return {
        "briefing": "\n".join(briefing_lines),
        "greeting": "GOOD MORNING, ROY.",
        "system_status": "All agents operational.",
        "active_missions": active,
        "highest_priority": next_action,
        "priority_analysis": orchestrator.store.priority_analysis(next_action) if next_action else None,
        "next_best_action": next_action["title"] if next_action else "No active missions.",
        "study": [m for m in active if m["category"] in ("ACCA", "University")],
        "projects": snapshot["projects"],
    }


@app.get("/api/projects")
def get_projects():
    return {"projects": orchestrator.store.projects()}


@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    detail = orchestrator.store.project_detail(project_id)
    return detail or {"error": "Project not found"}


@app.post("/api/projects")
def save_project(req: ProjectRequest):
    orchestrator.store.upsert_project(**req.model_dump())
    orchestrator.store.add_activity("Developer Agent", f"Updated project memory: {req.name}")
    return {"projects": orchestrator.store.projects()}


@app.post("/api/missions/{mission_id}/complete")
def complete_mission(mission_id: int):
    mission = orchestrator.store.complete_mission(mission_id)
    if not mission:
        return {"error": "Mission not found"}
    orchestrator.store.add_activity("Mission Control", f"Completed mission: {mission['title']}")
    return {"mission": mission}


@app.post("/api/missions/{mission_id}/status")
def update_mission_status(mission_id: int, req: MissionStatusRequest):
    mission = orchestrator.store.set_status(mission_id, req.status)
    if not mission:
        return {"error": "Mission not found or invalid status"}
    return {"mission": mission}


@app.post("/api/missions/{mission_id}/analyze")
def analyze_mission(mission_id: int):
    mission = orchestrator.agents["developer"].analyze_mission(mission_id)
    return {"mission": mission} if mission else {"error": "Programming mission not found or not eligible"}


@app.get("/api/missions/{mission_id}/plan")
def mission_plan(mission_id: int):
    mission = orchestrator.store.get_mission(mission_id)
    if not mission:
        return {"error": "Mission not found"}
    return {"mission_id": mission_id, "status": mission["status"], "plan": mission.get("plan", ""),
            "affected_files": mission.get("affected_files", "")}


@app.post("/api/missions/{mission_id}/approve")
def approve_mission(mission_id: int, req: ImplementationApprovalRequest):
    mission = orchestrator.store.get_mission(mission_id)
    if not mission or mission["category"] != "Programming":
        return {"error": "Programming mission not found"}
    if mission["status"] != "awaiting_approval":
        return {"error": "Mission must be awaiting approval"}
    mission = orchestrator.store.update_workflow(
        mission_id, implementation_changes=json.dumps(req.changes),
    )
    approved = orchestrator.store.approve_mission(mission_id, req.approved_by)
    orchestrator.store.add_activity("Developer Agent", f"Approved implementation for mission {mission_id}")
    return {"mission": approved}


@app.post("/api/missions/{mission_id}/implement")
def implement_mission(mission_id: int):
    mission = orchestrator.agents["developer"].implement_mission(mission_id)
    return {"mission": mission} if mission else {"error": "Mission must be an approved programming mission"}


@app.get("/api/missions/{mission_id}/results")
def mission_results(mission_id: int):
    mission = orchestrator.store.get_mission(mission_id)
    if not mission:
        return {"error": "Mission not found"}
    return {
        "mission_id": mission_id, "status": mission["status"],
        "implementation_result": mission.get("implementation_result", ""),
        "validation_result": mission.get("validation_result", ""),
        "files_modified": mission.get("files_modified", ""),
        "files_created": mission.get("files_created", ""),
    }


@app.get("/api/missions/{mission_id}/priority")
def mission_priority(mission_id: int):
    mission = orchestrator.store.get_mission(mission_id)
    return {"mission": mission, "analysis": orchestrator.store.priority_analysis(mission)} if mission else {"error": "Mission not found"}


@app.post("/api/missions/{mission_id}/subtasks")
def add_subtask(mission_id: int, req: SubtaskRequest):
    if not orchestrator.store.get_mission(mission_id):
        return {"error": "Mission not found"}
    subtask = orchestrator.store.add_subtask(mission_id, req.title, req.position)
    orchestrator.store.add_activity("Mission Control", f"Added subtask: {req.title}")
    return {"subtask": subtask, "subtasks": orchestrator.store.subtasks(mission_id)}


@app.post("/api/subtasks/{subtask_id}/status")
def update_subtask_status(subtask_id: int, req: SubtaskStatusRequest):
    subtask = orchestrator.store.set_subtask_status(subtask_id, req.status)
    return {"subtask": subtask} if subtask else {"error": "Subtask not found or invalid status"}


@app.get("/api/collaboration")
def collaboration():
    return {"handoffs": orchestrator.store.handoffs()}


@app.post("/api/task")
def submit_task(req: TaskRequest):
    result = orchestrator.route(req.text)
    history.append({"role": "user", "text": req.text})
    for r in result["results"]:
        history.append({"role": "agent", "agent": r["agent"], "text": r["reply"]})
    return result


app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
