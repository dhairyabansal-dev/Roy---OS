# Agent Bay — local automation crew

A small local multi-agent system: an orchestrator routes your requests to
specialist agents (email, files, scheduling), backed by a local LLM
(Ollama) or a fallback API, with a dashboard to talk to them.

## 1. Install Python deps

```bash
cd agent_system
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Set up the local model (recommended: Ollama, free, no GPU required)

1. Install Ollama: https://ollama.com
2. Pull a model:
   ```bash
  ollama pull qwen3:4b
   ```
3. Leave Ollama running in the background (it auto-starts a server on
   `localhost:11434`).

No GPU? It'll just run on CPU — slower, but works fine for short tasks.

Don't want to install anything local? Open `config.py`, set
`USE_OLLAMA = False`, and set the `LLM_API_KEY` environment variable to
an Anthropic (or other) API key.

## 3. (Optional) Connect email

Set these environment variables (use an **app password**, not your real
password — for Gmail: Google Account → Security → App Passwords):

```bash
export EMAIL_ADDRESS="you@gmail.com"
export EMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

Skip this if you only care about files/scheduling for now — the email
agent will just tell you it isn't connected.

## 4. Run it

```bash
python main.py
```

Then open **http://127.0.0.1:8000** in your browser. That's the dashboard.

## Windows launcher

### First-time setup

From the Agent Bay folder, install dependencies once. The launcher will use a
project virtual environment automatically when it exists:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3:4b
```

Ollama must be installed and available on `PATH` for local model commands.

### Start Agent Bay

Double-click `launcher\AgentBayLauncher.bat`. It locates the project root,
selects `.venv` or `venv`, checks Ollama and the configured model, prevents
duplicate servers, waits for the API, and opens the default browser at
`http://127.0.0.1:8000`. Backend output is written to
`data\agent_bay_server.log`.

To create a desktop shortcut without administrator permissions, run from
PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create_desktop_shortcut.ps1
```

The shortcut is named **Agent Bay**, uses a project icon when one exists, and
works regardless of the current terminal directory.

### Stop Agent Bay

Double-click `launcher\StopAgentBay.bat`, or run:

```powershell
python .\scripts\stop_agent_bay.py
```

This stops only the backend process started by the Agent Bay launcher. If the
launcher has not recorded a process, it leaves unrelated Python services
untouched.

## Mobile/LAN access

Agent Bay now binds to `0.0.0.0` by default so localhost remains available and
the active private LAN address can be reached from another device. Open the
Settings page to see the detected **Mobile Access** URL and scan its local QR
code. No cloud service is involved.

If you want to force localhost-only mode, launch it with:

```powershell
$env:AGENT_BAY_HOST = "127.0.0.1"
.\launcher\AgentBayLauncher.bat
```

The mobile URL is generated from an active private IPv4 address such as
`192.168.x.x` or `10.x.x.x`. If no Wi-Fi/Ethernet address is available, Settings
shows a helpful no-network message instead. This does not expose Agent Bay to
the public internet; keep Windows Firewall and your network trust settings in
mind.

## What each agent does today

| Agent    | Can do now                                              | Extend it in           |
|----------|----------------------------------------------------------|-------------------------|
| File     | Search files by keyword, dry-run "organize downloads"   | `agents/file_agent.py`  |
| Email    | Check unread, draft replies (with your confirmation)     | `agents/email_agent.py` |
| Schedule | Add/list/delete reminders in a local SQLite database     | `agents/schedule_agent.py` |
| Study | Create ACCA/university sessions and complete study missions | `agents/study_agent.py` |
| Quant | Organize quant finance project missions                | `agents/quant_agent.py` |
| Developer | Inspect agents and plan approval-gated enhancements | `agents/developer_agent.py` |

The Developer Agent recognizes requests such as “make the Email Agent capable of
cold emailing” and routes them to an inspection-first enhancement plan. It records
the plan as a programming mission and requires explicit approval before any
implementation work. The lightweight capability registry is available at
`/api/capabilities` and in `agents/capability_registry.py`.

Programming missions use a guarded lifecycle: `queued` -> `analyzing` ->
`awaiting_approval` -> `implementing` -> `validating` -> `completed` (or
`failed`). The Tasks view exposes Analyze, View Plan, Approve Implementation,
Start Implementation, and View Results actions when each action is valid. File
edits are project-root-only exact creates/modifications, protected files are
blocked, and validation is limited to fixed Python and JavaScript syntax checks.

Mission data, command history, project memory, activity, and priority inputs
are stored locally in `data/agent_bay.db`. The dashboard exposes `/api/status`,
`/api/briefing`, and mission completion/status endpoints. Priority scores are
transparent: explicit priority, deadline presence, importance, academic
relevance, project importance, and estimated workload are combined; missing
information contributes zero rather than being invented.

The orchestrator (`agents/orchestrator.py`) picks which agent(s) handle a
message — first by keyword matching, then by asking the LLM if nothing
matches.

## Safety notes

- The file agent **never deletes or moves files automatically** — it only
  searches and reports. Wire up real moves in `_organize_summary` once
  you trust it.
- The email agent **never sends automatically** — drafts are shown to you
  first. Call `EmailAgent.send()` yourself (or extend the dashboard with a
  "send" button) once you're happy with a draft.
- Scheduling is a local SQLite file — nothing leaves your machine unless
  you wire up a real calendar API.

## Extending with a new agent

1. Copy `agents/schedule_agent.py` as a template.
2. Implement `can_handle(text)` and `handle(text)`.
3. Register it in `Orchestrator.__init__` in `agents/orchestrator.py`.
4. It'll automatically show up in the dashboard's Crew sidebar.

## Swapping in a real calendar / smarter routing later

- Google Calendar: replace the SQLite calls in `schedule_agent.py` with
  the Google Calendar API (OAuth) — same `can_handle`/`handle` interface.
- Smarter routing / multi-step plans: look at **LangGraph** or **CrewAI**
  once this outgrows simple keyword routing.
