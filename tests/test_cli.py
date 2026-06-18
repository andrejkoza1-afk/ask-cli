"""Basic tests for ask-cli (no API calls required)."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ask_cli.cli import main
from ask_cli.config import _infer_provider, load_config


# ---------------------------------------------------------------------------
# CLI smoke tests (no LLM calls)
# ---------------------------------------------------------------------------

def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ask" in result.output.lower()


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_no_args_shows_usage():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

def test_load_config_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("ASK_CONFIG_DIR", str(tmp_path))
    cfg = load_config()
    assert isinstance(cfg, dict)


def test_infer_provider_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert _infer_provider() == "openai"


def test_infer_provider_anthropic(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert _infer_provider() == "anthropic"


def test_infer_provider_ollama_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert _infer_provider() == "ollama"


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

def test_unknown_provider_raises():
    from ask_cli.providers import stream_response
    with pytest.raises(ValueError, match="Unknown provider"):
        list(stream_response("unknown_provider", "model", None, []))


# ---------------------------------------------------------------------------
# Code block extraction
# ---------------------------------------------------------------------------

def test_extract_code_block():
    from ask_cli.cli import _extract_code_block
    text = "Some text\n```bash\nls -la\n```\nMore text"
    assert _extract_code_block(text) == "ls -la"


def test_extract_code_block_no_match():
    from ask_cli.cli import _extract_code_block
    assert _extract_code_block("No code here") is None
