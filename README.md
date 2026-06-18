<div align="center">

# ask

**AI terminal assistant. Ask anything, generate commands, write code — without leaving your shell.**

[![PyPI version](https://img.shields.io/pypi/v/ask-cli?color=blue)](https://pypi.org/project/ask-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/ask-cli)](https://pypi.org/project/ask-cli/)
[![CI](https://github.com/andrejkoza1-afk/ask-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/andrejkoza1-afk/ask-cli/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://static.pepy.tech/badge/ask-cli/month)](https://pepy.tech/project/ask-cli)

```
$ ask "how do I find all files larger than 100MB"

▸ openai/gpt-4o-mini · answer

Use the find command with -size flag:

  find / -type f -size +100M

  • /     — search root (replace with . for current directory)
  • -type f   — files only
  • -size +100M — larger than 100 megabytes

Add -ls to see sizes: find . -type f -size +100M -ls
```

</div>

---

## Why `ask`?

You're deep in a terminal session. You forget the exact `find` syntax. You need a quick Python snippet. You have an error log and no idea what it means.

Instead of alt-tabbing to a browser, context-switching to ChatGPT, and copying things back — you just type `ask`.

- **Zero config** — detects your API key automatically
- **Pipe-friendly** — `cat error.log | ask "what went wrong?"`
- **Shell mode** — describes what it will run *before* running it
- **Multi-provider** — OpenAI, Anthropic, Ollama (local/free), Groq
- **Streams live** — answers appear instantly, word by word
- **Tiny install** — two dependencies (`click` + `rich`)

---

## Install

```bash
pip install ask-cli
```

With your preferred provider:

```bash
pip install "ask-cli[openai]"      # OpenAI (GPT-4o, GPT-4o-mini…)
pip install "ask-cli[anthropic]"   # Anthropic (Claude)
pip install "ask-cli[groq]"        # Groq (fast + free tier)
pip install "ask-cli[all]"         # all providers
```

Ollama (local, no API key) works with zero extra packages — just run `ollama serve`.

---

## Quick start

**Set your API key** (once):

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Groq (free tier available at console.groq.com)
export GROQ_API_KEY=gsk_...

# Ollama — no key needed, just run: ollama serve
```

**Ask anything:**

```bash
ask "what is the difference between SIGTERM and SIGKILL"
```

---

## Usage

### Default — ask a question

```bash
ask "explain the CAP theorem in simple terms"
ask "what does inode mean in linux"
ask "how does TLS 1.3 differ from 1.2"
```

### `--sh` — generate a shell command

```bash
ask --sh "find all python files modified in the last 7 days"
ask --sh "show disk usage sorted by size, human readable"
ask --sh "watch a directory and notify when a file changes"
```

Output:
```
▸ openai/gpt-4o-mini · shell command

  find . -name "*.py" -mtime -7

# Finds all .py files in the current directory tree modified within the last 7 days.
```

### `--sh --run` — generate AND execute (with confirmation)

```bash
ask --sh --run "delete all .DS_Store files recursively"
```

```
▸ openai/gpt-4o-mini · shell command

  find . -name ".DS_Store" -delete

# Recursively removes all .DS_Store files from the current directory tree.

╭─ Command to run ──────────────────────────────────╮
│  find . -name ".DS_Store" -delete                  │
╰────────────────────────────────────────────────────╯
Run this command? [y/N]:
```

> `ask` always shows the command and asks for confirmation. It will **never** execute anything without your approval.

### `--code` — generate code

```bash
ask --code "write a python context manager for timing code blocks"
ask --code "bash script that monitors CPU usage and alerts above 90%"
ask --code "typescript function to debounce with generics"
```

### `--explain` — explain a shell command

```bash
ask --explain "find . -name '*.log' -mtime +30 -exec gzip {} +"
ask --explain "awk 'NR==FNR{a[$1]=$2; next} $1 in a {print $1, a[$1], $2}' file1 file2"
ask --explain "ss -tlnp | grep LISTEN"
```

### Pipe input

Pass any text through stdin — error messages, log files, code snippets:

```bash
# Diagnose an error
cat error.log | ask "what went wrong and how do I fix it?"

# Explain code
cat main.py | ask "explain what this script does"

# Review output
kubectl get pods | ask "are there any unhealthy pods?"

# Combine with a question
cat nginx.conf | ask "is there anything misconfigured here?"
```

### `--chat` — interactive chat session

```bash
ask --chat
```

```
╭──────────────────────────────────────────╮
│  ask — chat mode                         │
│  Model: openai/gpt-4o-mini               │
│                                          │
│  Type your message and press Enter.      │
│  Commands: /exit  /clear  /model <name>  │
╰──────────────────────────────────────────╯

you › how does async/await work in python?
ask › ...

you › can you show me an example with asyncio.gather?
ask › ...

you › /model claude-3-5-sonnet-20241022
      Switched to model: claude-3-5-sonnet-20241022

you › /exit
```

---

## Configuration

Create `~/.config/ask/config.toml`:

```toml
provider = "anthropic"
model    = "claude-3-5-sonnet-20241022"

# Or use environment variables (takes precedence):
# ASK_PROVIDER=openai
# ASK_MODEL=gpt-4o
# OPENAI_API_KEY=sk-...
```

### Environment variables

| Variable | Description |
|---|---|
| `ASK_PROVIDER` | Provider: `openai` / `anthropic` / `ollama` / `groq` |
| `ASK_MODEL` | Model name (e.g. `gpt-4o`, `claude-3-5-sonnet-20241022`) |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GROQ_API_KEY` | Groq API key |
| `ASK_CONFIG_DIR` | Override config directory |

### Provider defaults

| Provider | Default model | Notes |
|---|---|---|
| `openai` | `gpt-4o-mini` | Fast and cheap |
| `anthropic` | `claude-3-5-haiku-20241022` | Fast and cheap |
| `ollama` | `llama3.2` | Local, no API key |
| `groq` | `llama-3.3-70b-versatile` | Very fast, free tier |

---

## Shell integration

Add `ask` to your shell config for extra convenience:

**bash / zsh:**
```bash
# Quick alias: "?" instead of "ask"
alias ?='ask'

# Fix last command: explain the error
alias wtf='fc -ln -1 | ask "explain this error"'
```

**fish:**
```fish
alias ? ask
```

Now you can do: `? "how do I kill a process on port 3000"`

---

## Supported providers

| Provider | Models | API key required | Free tier |
|---|---|---|---|
| [OpenAI](https://platform.openai.com) | GPT-4o, GPT-4o-mini, o1, … | Yes | No |
| [Anthropic](https://console.anthropic.com) | Claude 3.5 Sonnet/Haiku, … | Yes | No |
| [Ollama](https://ollama.ai) | Llama 3, Mistral, Phi-3, … | No | ✅ Local |
| [Groq](https://console.groq.com) | Llama 3.3, Mixtral, … | Yes | ✅ Yes |

---

## Comparison

| Feature | `ask` | sgpt | llm | mods |
|---|:---:|:---:|:---:|:---:|
| Shell command mode | ✅ | ✅ | ❌ | ✅ |
| Confirmation before run | ✅ | ❌ | ❌ | ❌ |
| Pipe support | ✅ | ✅ | ✅ | ✅ |
| Ollama (local) | ✅ | ⚠️ | ✅ | ❌ |
| Groq | ✅ | ❌ | ✅ | ❌ |
| Interactive chat | ✅ | ✅ | ✅ | ❌ |
| Zero config | ✅ | ❌ | ❌ | ❌ |
| Pure Python + 2 deps | ✅ | ❌ | ❌ | ❌ |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/andrejkoza1-afk/ask-cli
cd ask-cli
pip install -e ".[dev]"
pytest tests/
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Made with ❤️ for terminal lovers. If `ask` saves you time, give it a ⭐

</div>
