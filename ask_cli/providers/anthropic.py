"""Anthropic Claude provider."""

from __future__ import annotations

from typing import Iterator


def stream(
    model: str,
    api_key: str | None,
    messages: list[dict],
) -> Iterator[str]:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for the Anthropic provider.\n"
            "Install it with:  pip install anthropic"
        )

    # Anthropic uses a separate system message
    system = None
    chat_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        else:
            chat_messages.append(msg)

    client = anthropic.Anthropic(api_key=api_key)

    kwargs: dict = dict(
        model=model,
        max_tokens=4096,
        messages=chat_messages,  # type: ignore[arg-type]
    )
    if system:
        kwargs["system"] = system

    with client.messages.stream(**kwargs) as stream_ctx:
        for text in stream_ctx.text_stream:
            yield text
