"""Ollama local provider (no API key needed)."""

from __future__ import annotations

import json
import urllib.request
from typing import Iterator

_DEFAULT_BASE = "http://localhost:11434"


def stream(
    model: str,
    messages: list[dict],
    base_url: str | None = None,
) -> Iterator[str]:
    base = (base_url or _DEFAULT_BASE).rstrip("/")
    url = f"{base}/api/chat"

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    break
    except OSError as exc:
        raise RuntimeError(
            f"Could not connect to Ollama at {base}.\n"
            "Make sure Ollama is running:  ollama serve\n"
            f"Error: {exc}"
        ) from exc
