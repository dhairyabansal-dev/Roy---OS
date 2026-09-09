import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import config


CATEGORIES = [
    "ACCA", "University", "Quant Finance", "Machine Learning", "Programming",
    "Hackathon", "Startup", "Portfolio", "Personal",
]
STATUSES = [
    "queued", "analyzing", "planned", "awaiting_approval", "implementing",
    "validating", "in_progress", "completed", "failed", "paused",
]
PROGRAMMING_STATUSES = {
    "queued", "analyzing", "planned", "awaiting_approval", "implementing",
    "validating", "completed", "failed",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class MissionStore:
    def __init__(self, path=None):
        self.path = path or config.MISSION_DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Personal',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    importance INTEGER NOT NULL DEFAULT 1,
                    academic_relevance INTEGER NOT NULL DEFAULT 0,
                    project_importance INTEGER NOT NULL DEFAULT 0,
                    estimated_minutes INTEGER,
                    deadline TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    objective TEXT DEFAULT '',
                    current_phase TEXT DEFAULT '',
                    progress INTEGER NOT NULL DEFAULT 0,
                    assigned_agent TEXT DEFAULT '',
                    project_id INTEGER,
                    target_agent TEXT DEFAULT '',
                    enhancement_request TEXT DEFAULT '',
                    plan TEXT DEFAULT '',
                    affected_files TEXT DEFAULT '',
                    implementation_result TEXT DEFAULT '',
                    validation_result TEXT DEFAULT '',
                    approval_at TEXT,
                    approved_by TEXT DEFAULT '',
                    files_modified TEXT DEFAULT '',
                    files_created TEXT DEFAULT '',
                    capabilities_added TEXT DEFAULT '',
                    implementation_changes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    result TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    objective TEXT DEFAULT '',
                    current_phase TEXT DEFAULT '',
                    technologies TEXT DEFAULT '',
                    agents_involved TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    next_action TEXT DEFAULT '',
                    important_files TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subtasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    position INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS agent_handoffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id INTEGER,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    agent_key TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_agent_updated
                    ON conversations(agent_key, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                    ON messages(conversation_id, id);
                """
            )
            self._ensure_columns(conn, "missions", {
                "objective": "TEXT DEFAULT ''", "current_phase": "TEXT DEFAULT ''",
                "progress": "INTEGER NOT NULL DEFAULT 0", "assigned_agent": "TEXT DEFAULT ''",
                "project_id": "INTEGER",
                "target_agent": "TEXT DEFAULT ''", "enhancement_request": "TEXT DEFAULT ''",
                "plan": "TEXT DEFAULT ''", "affected_files": "TEXT DEFAULT ''",
                "implementation_result": "TEXT DEFAULT ''", "validation_result": "TEXT DEFAULT ''",
                "approval_at": "TEXT", "approved_by": "TEXT DEFAULT ''",
                "files_modified": "TEXT DEFAULT ''", "files_created": "TEXT DEFAULT ''",
                "capabilities_added": "TEXT DEFAULT ''", "implementation_changes": "TEXT DEFAULT ''",
            })
            self._ensure_columns(conn, "projects", {
                "current_phase": "TEXT DEFAULT ''", "technologies": "TEXT DEFAULT ''",
                "agents_involved": "TEXT DEFAULT ''",
            })

    @staticmethod
    def _ensure_columns(conn, table, columns):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def create_mission(self, title, category="Personal", priority="medium", estimated_minutes=None,
                       deadline=None, importance=1, academic_relevance=0, project_importance=0,
                       objective="", current_phase="", progress=0, assigned_agent="", project_id=None,
                       status="queued", target_agent="", enhancement_request="", plan="",
                       affected_files="", implementation_result="", validation_result="",
                       approval_at=None, approved_by="", files_modified="", files_created="",
                       capabilities_added="", implementation_changes=""):
        category = category if category in CATEGORIES else "Personal"
        priority = priority if priority in ("low", "medium", "high", "urgent") else "medium"
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO missions
                (title, category, priority, importance, academic_relevance, project_importance,
                 estimated_minutes, deadline, objective, current_phase, progress, assigned_agent,
                 project_id, status, target_agent, enhancement_request, plan, affected_files,
                 implementation_result, validation_result, approval_at, approved_by, files_modified,
                 files_created, capabilities_added, implementation_changes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, category, priority, importance, academic_relevance, project_importance,
                 estimated_minutes, deadline, objective, current_phase, max(0, min(progress, 100)),
                 assigned_agent, project_id, status if status in STATUSES else "queued", target_agent,
                 enhancement_request, plan, affected_files, implementation_result, validation_result,
                 approval_at, approved_by, files_modified, files_created, capabilities_added,
                 implementation_changes, now_iso()),
            )
            mission_id = cursor.lastrowid
        return self.get_mission(mission_id)

    def get_mission(self, mission_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)).fetchone()
            return dict(row) if row else None

    def list_missions(self, status=None, category=None, limit=50):
        query = "SELECT * FROM missions"
        params = []
        clauses = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if category:
            clauses.append("category = ?")
            params.append(category)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def complete_mission(self, mission_id):
        with self._connect() as conn:
            conn.execute("UPDATE missions SET status = 'completed', completed_at = ? WHERE id = ?", (now_iso(), mission_id))
        return self.get_mission(mission_id)

    def update_workflow(self, mission_id, status=None, progress=None, current_phase=None, **fields):
        """Update one programming workflow atomically and return the mission."""
        allowed = {
            "plan", "affected_files", "implementation_result", "validation_result",
            "approval_at", "approved_by", "files_modified", "files_created",
            "capabilities_added", "implementation_changes", "target_agent", "enhancement_request", "objective",
        }
        updates = {}
        if status is not None and status in STATUSES:
            updates["status"] = status
        if progress is not None:
            updates["progress"] = max(0, min(int(progress), 100))
        if current_phase is not None:
            updates["current_phase"] = current_phase
        updates.update({key: value for key, value in fields.items() if key in allowed})
        if not updates:
            return self.get_mission(mission_id)
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self._connect() as conn:
            conn.execute(f"UPDATE missions SET {assignments} WHERE id = ?", (*updates.values(), mission_id))
        return self.get_mission(mission_id)

    def approve_mission(self, mission_id, approved_by="user"):
        mission = self.get_mission(mission_id)
        if not mission or mission["category"] != "Programming" or mission["status"] != "awaiting_approval":
            return None
        return self.update_workflow(
            mission_id, status="implementing", progress=60, current_phase="implementing",
            approval_at=now_iso(), approved_by=approved_by,
        )

    def set_status(self, mission_id, status):
        if status not in STATUSES:
            return None
        mission = self.get_mission(mission_id)
        if not mission:
            return None
        if mission["category"] == "Programming" and status in PROGRAMMING_STATUSES:
            return None
        with self._connect() as conn:
            conn.execute("UPDATE missions SET status = ? WHERE id = ?", (status, mission_id))
        return self.get_mission(mission_id)

    def record_command(self, command, agent, result, status="completed"):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO command_history (command, agent, result, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (command, agent, result, status, now_iso()),
            )

    def history(self, limit=50):
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM command_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()]

    def add_activity(self, agent, message):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO activity (agent, message, created_at) VALUES (?, ?, ?)",
                (agent, message, now_iso()),
            )

    def activities(self, limit=30):
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()]

    def upsert_project(self, name, description="", objective="", current_phase="", technologies="",
                       agents_involved="", status="active", next_action="", important_files="", notes=""):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO projects
                (name, description, objective, current_phase, technologies, agents_involved, status,
                 next_action, important_files, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET description=excluded.description, objective=excluded.objective,
                current_phase=excluded.current_phase, technologies=excluded.technologies,
                agents_involved=excluded.agents_involved,
                status=excluded.status, next_action=excluded.next_action, important_files=excluded.important_files,
                notes=excluded.notes, updated_at=excluded.updated_at""",
                (name, description, objective, current_phase, technologies, agents_involved, status,
                 next_action, important_files, notes, now_iso()),
            )

    def projects(self):
        with self._connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()]

    def project_detail(self, project_id):
        with self._connect() as conn:
            project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not project:
                return None
            missions = conn.execute(
                "SELECT * FROM missions WHERE project_id = ? ORDER BY created_at DESC", (project_id,)
            ).fetchall()
            return {"project": dict(project), "missions": [dict(row) for row in missions]}

    def add_subtask(self, mission_id, title, position=0):
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO subtasks (mission_id, title, position, created_at) VALUES (?, ?, ?, ?)",
                (mission_id, title, position, now_iso()),
            )
            subtask_id = cursor.lastrowid
        return self.get_subtask(subtask_id)

    def get_subtask(self, subtask_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,)).fetchone()
            return dict(row) if row else None

    def subtasks(self, mission_id):
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM subtasks WHERE mission_id = ? ORDER BY position, id", (mission_id,)
            ).fetchall()]

    def set_subtask_status(self, subtask_id, status):
        if status not in ("pending", "completed", "skipped"):
            return None
        with self._connect() as conn:
            conn.execute(
                "UPDATE subtasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, now_iso() if status == "completed" else None, subtask_id),
            )
            row = conn.execute("SELECT mission_id FROM subtasks WHERE id = ?", (subtask_id,)).fetchone()
            if row:
                total = conn.execute("SELECT COUNT(*) FROM subtasks WHERE mission_id = ?", (row[0],)).fetchone()[0]
                done = conn.execute("SELECT COUNT(*) FROM subtasks WHERE mission_id = ? AND status = 'completed'", (row[0],)).fetchone()[0]
                if total:
                    conn.execute("UPDATE missions SET progress = ? WHERE id = ?", (round(done / total * 100), row[0]))
        return self.get_subtask(subtask_id)

    def add_handoff(self, mission_id, from_agent, to_agent, payload):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO agent_handoffs (mission_id, from_agent, to_agent, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (mission_id, from_agent, to_agent, payload, now_iso()),
            )

    def handoffs(self, mission_id=None):
        query = "SELECT * FROM agent_handoffs"
        params = []
        if mission_id:
            query += " WHERE mission_id = ?"
            params.append(mission_id)
        query += " ORDER BY id DESC LIMIT 50"
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def default_conversation(self, agent_key) -> dict:
        """Return the durable default direct-chat conversation for one agent."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE agent_key = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
                (agent_key,),
            ).fetchone()
            if row:
                return dict(row)
            timestamp = now_iso()
            cursor = conn.execute(
                "INSERT INTO conversations (agent_key, created_at, updated_at) VALUES (?, ?, ?)",
                (agent_key, timestamp, timestamp),
            )
            conversation_id = cursor.lastrowid
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise RuntimeError("Conversation could not be created.")
        return conversation

    def get_conversation(self, conversation_id) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            return dict(row) if row else None

    def conversation_messages(self, agent_key, limit=100):
        conversation = self.default_conversation(agent_key)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
                (conversation["id"], limit),
            ).fetchall()
        return conversation, [dict(row) for row in reversed(rows)]

    def add_conversation_message(self, agent_key, role, content):
        if role not in ("user", "agent", "system"):
            raise ValueError("Invalid conversation message role.")
        conversation = self.default_conversation(agent_key)
        timestamp = now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO messages (conversation_id, agent_key, role, content, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (conversation["id"], agent_key, role, content, timestamp),
            )
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (timestamp, conversation["id"]))
            message_id = cursor.lastrowid
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
            return dict(row)

    def snapshot(self):
        missions = self.list_missions()
        active = [m for m in missions if m["status"] not in ("completed", "failed")]
        completed_today = [m for m in missions if m["status"] == "completed" and m["completed_at"] and m["completed_at"][:10] == now_iso()[:10]]
        return {
            "missions": missions,
            "active_missions": active,
            "completed_today": completed_today,
            "projects": self.projects(),
            "activity": self.activities(),
            "history": self.history(),
        }

    @staticmethod
    def priority_score(mission):
        priority_points = {"low": 1, "medium": 2, "high": 4, "urgent": 6}
        deadline_points = 0
        if mission.get("deadline"):
            deadline_points = 3
        workload_points = min((mission.get("estimated_minutes") or 60) / 60, 4)
        return round(
            priority_points.get(mission.get("priority"), 2)
            + deadline_points
            + mission.get("importance", 0)
            + mission.get("academic_relevance", 0)
            + mission.get("project_importance", 0)
            + workload_points,
            1,
        )

    def next_best_action(self):
        missions = [m for m in self.list_missions() if m["status"] in ("queued", "in_progress", "paused")]
        if not missions:
            return None
        return max(missions, key=self.priority_score)

    def priority_analysis(self, mission):
        urgency = 4 if mission.get("priority") in ("high", "urgent") else 2
        urgency += 3 if mission.get("deadline") else 0
        impact = min(mission.get("importance", 0) + mission.get("project_importance", 0), 6)
        academic = min(mission.get("academic_relevance", 0), 4)
        momentum = 2 if mission.get("status") == "in_progress" else 1
        effort = max(1, 5 - round((mission.get("estimated_minutes") or 60) / 60))
        score = self.priority_score(mission)
        return {
            "score": round(min(score / 2, 10), 1),
            "urgency": min(urgency, 10), "impact": min(impact + academic, 10),
            "momentum": momentum, "effort": effort,
            "reason": "High-impact active work with explicit priority inputs." if momentum > 1 else "Highest available score from stored priority inputs.",
        }
