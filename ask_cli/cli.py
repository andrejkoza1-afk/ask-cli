"""ask — AI terminal assistant.

Usage examples
--------------
ask "how do I find all files larger than 100MB"
ask --sh "delete node_modules recursively"
ask --code "write a fibonacci generator in python"
ask --explain "awk '{print $2}' access.log"
cat error.log | ask "what went wrong?"
ask --chat
"""

from __future__ import annotations

import os
import select
import subprocess
import sys
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.text import Text

from .config import get_api_key, get_config_dir, get_model, get_provider, load_config
from .providers import stream_response

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM_DEFAULT = """\
You are a concise, expert developer assistant running inside a terminal.
- Answer directly and briefly. Avoid unnecessary preamble.
- Use markdown for code blocks, headers, and lists when it helps readability.
- Prefer practical, copy-paste-ready answers.
"""

_SYSTEM_SHELL = """\
You are an expert shell command generator.
The user will describe what they want to do. You must:
1. Output ONLY the shell command(s) — nothing else on the first code block.
2. After the code block, add a brief one-line explanation prefixed with "# ".
3. If multiple commands are needed, chain them or show them in order.
4. Use POSIX-compatible syntax unless the user specifies otherwise.
5. Never include commentary before the command block.

Example response format:
```bash
find . -name "node_modules" -type d -prune -exec rm -rf {} +
```
# Recursively finds and deletes all node_modules directories from the current path.
"""

_SYSTEM_CODE = """\
You are an expert programmer. When asked to write code:
1. Output ONLY the code in a properly-typed code block (e.g. ```python).
2. Follow it with a brief explanation (2-4 sentences max).
3. Prefer clean, idiomatic, production-ready code.
4. Add type hints for Python. Add JSDoc for JavaScript/TypeScript.
"""

_SYSTEM_EXPLAIN = """\
You are a shell command explainer. Given a shell command:
1. Explain what the command does in plain English (1-2 sentences).
2. Then break down each flag/argument in a table: | flag | meaning |
3. Add a "Watch out for" section only if there are gotchas.
Keep it short — developers are busy.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pipe_input() -> Optional[str]:
    """Read from stdin if data is being piped in."""
    try:
        if not sys.stdin.isatty():
            return sys.stdin.read().strip()
    except Exception:
        pass
    return None


def _extract_code_block(text: str) -> Optional[str]:
    """Extract the first fenced code block from a markdown response."""
    import re
    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _collect_stream(
    provider: str,
    model: str,
    api_key: Optional[str],
    messages: list[dict],
    base_url: Optional[str],
    live_render: bool = True,
) -> str:
    """Stream the response, optionally printing live, and return full text."""
    chunks = []

    if live_render:
        with console.status("", spinner="dots") as status:
            status.stop()  # we print live instead
            for chunk in stream_response(provider, model, api_key, messages, base_url):
                console.print(chunk, end="", highlight=False)
                chunks.append(chunk)
        console.print()  # newline after stream
    else:
        for chunk in stream_response(provider, model, api_key, messages, base_url):
            chunks.append(chunk)

    return "".join(chunks)


def _render_response(text: str, mode: str) -> None:
    """Pretty-print the final response using rich markdown."""
    console.print()
    if mode in ("default", "explain", "code"):
        console.print(Markdown(text))
    elif mode == "shell":
        console.print(Markdown(text))
    console.print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", nargs=-1)
@click.option("--sh", "mode", flag_value="shell", help="Generate a shell command from natural language.")
@click.option("--code", "mode", flag_value="code", help="Generate code from a description.")
@click.option("--explain", "mode", flag_value="explain", help="Explain a shell command.")
@click.option("--chat", "mode", flag_value="chat", help="Start an interactive chat session.")
@click.option("--run", is_flag=True, default=False, help="Auto-run the generated shell command (prompts for confirmation).")
@click.option("--model", "-m", default=None, help="Override the model (e.g. gpt-4o, claude-3-5-sonnet-20241022).")
@click.option("--provider", "-p", default=None, help="Override the provider (openai | anthropic | ollama | groq).")
@click.option("--url", default=None, help="Custom base URL for the API (e.g. for self-hosted Ollama).")
@click.option("--no-md", is_flag=True, default=False, help="Print plain text without markdown rendering.")
@click.version_option(package_name="ask-cli")
def main(
    query: tuple[str, ...],
    mode: Optional[str],
    run: bool,
    model: Optional[str],
    provider: Optional[str],
    url: Optional[str],
    no_md: bool,
) -> None:
    """
    \b
    ╔═══════════════════════════════════════╗
    ║  ask — AI terminal assistant          ║
    ╚═══════════════════════════════════════╝

    \b
    Examples:
      ask "how do I recursively find large files"
      ask --sh "delete all .DS_Store files"
      ask --sh --run "show disk usage by folder"
      ask --code "fibonacci generator in rust"
      ask --explain "grep -rn --include='*.py' 'TODO'"
      cat error.log | ask "what went wrong?"
      ask --chat
    """
    # ------------------------------------------------------------------ setup
    cfg = load_config()
    _provider = provider or get_provider(cfg)
    _model = model or get_model(cfg, _provider)
    _api_key = get_api_key(cfg, _provider)

    if mode is None:
        mode = "default"

    # ------------------------------------------------------------------ chat mode
    if mode == "chat":
        _run_chat(_provider, _model, _api_key, url, no_md)
        return

    # ------------------------------------------------------------------ build prompt
    pipe = _pipe_input()
    user_text = " ".join(query).strip()

    if not user_text and not pipe:
        console.print(
            Panel(
                "[bold]Usage:[/bold]  ask [OPTIONS] [QUERY]\n\n"
                "Run [bold]ask --help[/bold] to see all options.",
                title="[bold cyan]ask[/bold cyan]",
                border_style="cyan",
            )
        )
        sys.exit(0)

    if pipe and user_text:
        prompt = f"{user_text}\n\n```\n{pipe}\n```"
    elif pipe:
        prompt = pipe
    else:
        prompt = user_text

    system_prompts = {
        "default": _SYSTEM_DEFAULT,
        "shell": _SYSTEM_SHELL,
        "code": _SYSTEM_CODE,
        "explain": _SYSTEM_EXPLAIN,
    }
    system = system_prompts.get(mode, _SYSTEM_DEFAULT)

    if mode == "explain" and not pipe:
        # Wrap the query so it reads as a command to explain
        prompt = f"Explain this command:\n```\n{prompt}\n```"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    # ------------------------------------------------------------------ header
    mode_labels = {
        "default": "answer",
        "shell": "shell command",
        "code": "code",
        "explain": "explanation",
    }
    label = mode_labels.get(mode, mode)
    console.print(
        f"[dim]▸ {_provider}/{_model} · {label}[/dim]"
    )

    # ------------------------------------------------------------------ stream
    try:
        response_text = _collect_stream(_provider, _model, _api_key, messages, url, live_render=no_md is False)
    except RuntimeError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(0)

    if not no_md and mode not in ("default",):
        # Already streamed raw; re-render as markdown for non-default modes
        pass  # live stream already printed; markdown was implicit

    # ------------------------------------------------------------------ --run
    if run and mode == "shell":
        cmd = _extract_code_block(response_text)
        if cmd:
            console.print()
            console.print(
                Panel(
                    Syntax(cmd, "bash", theme="monokai", word_wrap=True),
                    title="[bold yellow]Command to run[/bold yellow]",
                    border_style="yellow",
                )
            )
            if Confirm.ask("[bold yellow]Run this command?[/bold yellow]", default=False):
                console.print()
                result = subprocess.run(cmd, shell=True)
                if result.returncode != 0:
                    err_console.print(f"[red]Exit code {result.returncode}[/red]")
                    sys.exit(result.returncode)
            else:
                console.print("[dim]Aborted.[/dim]")
        else:
            console.print("[yellow]Could not extract a command to run.[/yellow]")


# ---------------------------------------------------------------------------
# Interactive chat
# ---------------------------------------------------------------------------

def _run_chat(
    provider: str,
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
    no_md: bool,
) -> None:
    console.print(
        Panel(
            f"[bold cyan]ask — chat mode[/bold cyan]\n"
            f"[dim]Model: {provider}/{model}[/dim]\n\n"
            "Type your message and press Enter.\n"
            "[dim]Commands: /exit  /clear  /model <name>  /help[/dim]",
            border_style="cyan",
        )
    )

    history: list[dict] = [{"role": "system", "content": _SYSTEM_DEFAULT}]

    while True:
        try:
            user_input = console.input("[bold cyan]you[/bold cyan] › ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        # Built-in slash commands
        if user_input.startswith("/"):
            cmd_parts = user_input[1:].split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

            if cmd in ("exit", "quit", "q"):
                console.print("[dim]Goodbye.[/dim]")
                break
            elif cmd == "clear":
                history = [history[0]]  # keep system prompt
                console.clear()
                console.print("[dim]Context cleared.[/dim]")
            elif cmd == "model" and arg:
                model = arg
                console.print(f"[dim]Switched to model: {model}[/dim]")
            elif cmd == "help":
                console.print(
                    "[dim]/exit[/dim]  — quit\n"
                    "[dim]/clear[/dim] — clear context\n"
                    "[dim]/model <name>[/dim] — switch model"
                )
            else:
                console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
            continue

        history.append({"role": "user", "content": user_input})

        console.print(f"\n[bold green]ask[/bold green] › ", end="")
        try:
            response = _collect_stream(provider, model, api_key, history, base_url, live_render=True)
        except RuntimeError as exc:
            err_console.print(f"[bold red]Error:[/bold red] {exc}")
            history.pop()  # remove failed user message
            continue
        except KeyboardInterrupt:
            console.print("\n[dim](interrupted)[/dim]")
            history.pop()
            continue

        history.append({"role": "assistant", "content": response})
        console.print()


if __name__ == "__main__":
    main()
