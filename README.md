# coding-agent

A minimal Claude-Code-style coding agent CLI. Talks to any OpenAI-compatible
endpoint (Ollama, llama.cpp, LM Studio, or OpenAI) with tool calling.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14+.

```bash
uv sync
```

Pull a tool-capable local model (example with Ollama):

```bash
ollama pull qwen2.5-coder:14b
ollama serve
```

## Usage

```bash
uv run coding-agent chat --model qwen2.5-coder:14b
```

Or:

```bash
uv run python -m coding_agent chat --model qwen2.5-coder:14b
```

Flags:

| Flag | Meaning |
|------|---------|
| `--model` | Model name on your server (default: `qwen2.5-coder:14b`) |
| `--base-url` | OpenAI-compatible base URL (default: `http://localhost:11434/v1`) |
| `--api-key` | API key (default: `ollama`; ignored by most local servers) |
| `--yolo` | Skip confirmation prompts on writes/edits/shell |

Type `/exit` or `/quit` (or Ctrl-C) to leave the session.

## Architecture

```
user input
  → append to conversation history
  → call model with [system prompt + history + tool schemas]
  → model returns text OR tool_calls
  → if tool_calls: execute each, append results, loop
  → if text: print it, wait for next user input
```

Tools: `read_file`, `list_dir`, `search_code` (read-only); `write_file`,
`edit_file`, `run_shell` (gated behind confirmation unless `--yolo`).

Package layout lives under `src/coding_agent/` — agent loop, CLI, prompts, and
tools are separate modules so you can extend them independently.

## Development

```bash
uv sync --group dev
uv run ruff check src tests          # lint
uv run ruff format src tests         # format
uv run mypy                          # type check
uv run pytest                        # tests
```

One-shot check (format check + lint + types + tests):

```bash
uv run ruff format --check src tests && uv run ruff check src tests && uv run mypy && uv run pytest
```
