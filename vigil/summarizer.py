import json
import os
import time
import urllib.request

_cache: dict[str, tuple[str, float]] = {}
_TTL = 20  # seconds between refreshes per agent

OLLAMA_LOCAL_URL = "http://localhost:11434/api/chat"
OLLAMA_CLOUD_URL = "https://api.ollama.com/api/chat"
OLLAMA_MODEL     = os.environ.get("VIGIL_OLLAMA_MODEL", "llama3.2")

_PROMPT = (
    "Last lines of a terminal process:\n\n"
    "{output}\n\n"
    "One sentence: what is this process doing right now? BE SPECIFIC. NO PREAMBLE."
)


def _ollama(output: str) -> str | None:
    api_key = os.environ.get("OLLAMA_API_KEY")
    url     = OLLAMA_CLOUD_URL if api_key else OLLAMA_LOCAL_URL

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": _PROMPT.format(output=output)}],
        "stream": False,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())["message"]["content"].strip()
    except Exception:
        return None


def _anthropic(output: str) -> str | None:
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=80,
            messages=[{"role": "user", "content": _PROMPT.format(output=output)}],
        )
        return response.content[0].text.strip()
    except Exception:
        return None


def summarize(name: str, output: str) -> str | None:
    if not output.strip():
        return None

    now = time.time()
    cached_summary, cached_at = _cache.get(name, ("", 0.0))
    if cached_at and now - cached_at < _TTL:
        return cached_summary

    summary = _ollama(output) or _anthropic(output)

    if summary:
        _cache[name] = (summary, now)
    return summary
