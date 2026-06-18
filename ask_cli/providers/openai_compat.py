"""OpenAI-compatible provider (works for OpenAI, Groq, any OpenAI-API endpoint)."""

from __future__ import annotations

from typing import Iterator

_GROQ_BASE = "https://api.groq.com/openai/v1"
_OPENAI_BASE = "https://api.openai.com/v1"


def stream(
    model: str,
    api_key: str | None,
    messages: list[dict],
    base_url: str | None,
    provider: str = "openai",
) -> Iterator[str]:
    try:
        from openai import OpenAI, APIConnectionError, AuthenticationError
    except ImportError:
        raise ImportError(
            "The 'openai' package is required for OpenAI/Groq providers.\n"
            "Install it with:  pip install openai"
        )

    if base_url is None:
        base_url = _GROQ_BASE if provider == "groq" else _OPENAI_BASE

    client = OpenAI(api_key=api_key or "sk-none", base_url=base_url)

    try:
        with client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        ) as stream_ctx:
            for chunk in stream_ctx:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
    except AuthenticationError:
        raise RuntimeError(
            "Authentication failed. Check your API key.\n"
            "Set it with:  export OPENAI_API_KEY=sk-..."
        )
    except APIConnectionError as exc:
        raise RuntimeError(f"Could not connect to {provider}: {exc}") from exc
