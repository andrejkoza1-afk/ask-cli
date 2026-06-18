"""Configuration management for ask-cli."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CONFIG_DIR = Path(os.environ.get("ASK_CONFIG_DIR", Path.home() / ".config" / "ask"))
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


# ---------------------------------------------------------------------------
# Config loading (toml, with fallback to env vars)
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load config from ~/.config/ask/config.toml, falling back to env vars."""
    cfg: dict = {}

    if CONFIG_FILE.exists():
        try:
            if sys.version_info >= (3, 11):
                import tomllib
                with open(CONFIG_FILE, "rb") as f:
                    cfg = tomllib.load(f)
            else:
                try:
                    import tomli
                    with open(CONFIG_FILE, "rb") as f:
                        cfg = tomli.load(f)
                except ImportError:
                    pass  # fall through to env vars
        except Exception:
            pass

    return cfg


def get_provider(cfg: dict) -> str:
    return (
        os.environ.get("ASK_PROVIDER")
        or cfg.get("provider")
        or _infer_provider()
    )


def _infer_provider() -> str:
    """Guess provider from available API keys."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "ollama"


def get_model(cfg: dict, provider: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "ollama": "llama3.2",
        "groq": "llama-3.3-70b-versatile",
    }
    return (
        os.environ.get("ASK_MODEL")
        or cfg.get("model")
        or defaults.get(provider, "gpt-4o-mini")
    )


def get_api_key(cfg: dict, provider: str) -> Optional[str]:
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    env_var = env_keys.get(provider)
    if env_var:
        return os.environ.get(env_var) or cfg.get("api_key")
    return None
