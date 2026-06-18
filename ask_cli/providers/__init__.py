"""LLM provider registry."""

from __future__ import annotations

from typing import Iterator


def stream_response(
    provider: str,
    model: str,
    api_key: str | None,
    messages: list[dict],
    base_url: str | None = None,
) -> Iterator[str]:
    """Dispatch to the right provider and yield streamed text chunks."""
    if provider == "ollama":
        from .ollama import stream as _stream
        yield from _stream(model, messages, base_url)
    elif provider in ("openai", "groq"):
        from .openai_compat import stream as _stream
        yield from _stream(model, api_key, messages, base_url, provider)
    elif provider == "anthropic":
        from .anthropic import stream as _stream
        yield from _stream(model, api_key, messages)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Supported: openai, anthropic, ollama, groq")
