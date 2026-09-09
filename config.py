"""
Central configuration for the local agent system.
Edit these values to match your setup.
"""

import os


def _environment_value(name, default=""):
	"""Read process env first, then the Windows user env scope after setx."""
	value = os.getenv(name)
	if value:
		return value.strip()
	if os.name == "nt":
		try:
			import winreg

			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
				value, _ = winreg.QueryValueEx(key, name)
				return str(value).strip()
		except (FileNotFoundError, OSError):
			pass
	return default


def credential_presence():
	"""Return safe configuration diagnostics without exposing credential values."""
	return {
		"EMAIL_ADDRESS": bool(_environment_value("EMAIL_ADDRESS")),
		"EMAIL_APP_PASSWORD": bool(_environment_value("EMAIL_APP_PASSWORD")),
	}

# ---- LLM settings ----
# Uses Ollama by default (https://ollama.com) - install it, then run:
#   ollama pull qwen3:4b
# If you don't have Ollama / GPU, set USE_OLLAMA = False and fill in an API key
# to fall back to a hosted model instead.

USE_OLLAMA = True
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")  # override with an installed model

# Fallback hosted model (only used if USE_OLLAMA = False)
FALLBACK_API_KEY = os.environ.get("LLM_API_KEY", "")
FALLBACK_API_URL = "https://api.anthropic.com/v1/messages"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"

# ---- File agent settings ----
FILE_AGENT_ROOT = os.path.expanduser("~")   # folder the file agent is allowed to touch
FILE_AGENT_ALLOWED_EXT = [".txt", ".pdf", ".docx", ".csv", ".md", ".jpg", ".png"]

# ---- Email agent settings (IMAP/SMTP) ----
EMAIL_IMAP_HOST = "imap.gmail.com"
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_ADDRESS = _environment_value("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = _environment_value("EMAIL_APP_PASSWORD")  # use an app password, not your real password

# ---- Scheduling agent settings ----
# Uses a local SQLite file so it works with zero setup.
# (Swap for Google Calendar API later if you want real calendar sync.)
SCHEDULE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "schedule.db")
MISSION_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "agent_bay.db")

# ---- Server ----
# Keep localhost as the secure default. Set AGENT_BAY_HOST=0.0.0.0 only when
# you intentionally want to use Agent Bay from another device on your LAN.
HOST = os.environ.get("AGENT_BAY_HOST", "0.0.0.0")
PORT = int(os.environ.get("AGENT_BAY_PORT", "8000"))
