"""
Thin wrapper so the rest of the code doesn't care whether the model
is running locally via Ollama or through a hosted API.
"""

import json
import requests
import config


def chat(messages, system=None, max_tokens=800):
    """
    messages: list of {"role": "user"|"assistant", "content": "..."}
    system: optional system prompt string
    Returns: assistant reply text (str)
    """
    if config.USE_OLLAMA:
        return _chat_ollama(messages, system)
    return _chat_fallback(messages, system, max_tokens)


def _chat_ollama(messages, system):
    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    try:
        resp = requests.post(
            config.OLLAMA_URL,
            json={
                "model": config.OLLAMA_MODEL,
                "messages": payload_messages,
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        return (
            "[Error] Couldn't reach Ollama at "
            f"{config.OLLAMA_URL}. Is it installed and running? "
            "Install: https://ollama.com  |  Then run: ollama pull "
            f"{config.OLLAMA_MODEL}"
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return (
                f"[Error] Ollama model '{config.OLLAMA_MODEL}' was not found. "
                f"Run `ollama list`, then set OLLAMA_MODEL to an installed model "
                f"or run `ollama pull {config.OLLAMA_MODEL}`."
            )
        return f"[Error] Ollama request failed: {e}"
    except Exception as e:
        return f"[Error] Ollama request failed: {e}"


def _chat_fallback(messages, system, max_tokens):
    if not config.FALLBACK_API_KEY:
        return "[Error] No FALLBACK_API_KEY set and USE_OLLAMA is False. Set one in config.py or env vars."

    try:
        resp = requests.post(
            config.FALLBACK_API_URL,
            headers={
                "x-api-key": config.FALLBACK_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.FALLBACK_MODEL,
                "max_tokens": max_tokens,
                "system": system or "",
                "messages": messages,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(parts).strip()
    except Exception as e:
        return f"[Error] Fallback API request failed: {e}"
