# Contributing to ask-cli

Thank you for your interest in contributing! Here's how to get started.

## Development setup

```bash
git clone https://github.com/yourusername/ask-cli
cd ask-cli
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,all]"
```

## Running tests

```bash
pytest tests/ -v
```

## Running the linter

```bash
ruff check ask_cli/
ruff format ask_cli/
```

## Adding a new provider

1. Create `ask_cli/providers/<name>.py` with a `stream(model, api_key, messages, ...)` function that yields text chunks.
2. Register it in `ask_cli/providers/__init__.py`.
3. Add defaults to `ask_cli/config.py`.
4. Add an optional dependency in `pyproject.toml`.
5. Update the README provider table.

## Pull request guidelines

- Keep PRs focused — one feature or fix per PR.
- Add tests for new functionality.
- Update the README if you add user-facing changes.
- Run `ruff check` and `pytest` before submitting.

## Reporting bugs

Open an issue with:
- Your OS and Python version
- The command you ran
- The full error output
