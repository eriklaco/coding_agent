"""Code search tool (ripgrep if available, else grep)."""

from __future__ import annotations

import shutil
import subprocess

from coding_agent.tools.base import ToolSpec

_EXCLUDE_DIRS = (
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".eggs",
)


def search_code(pattern: str, path: str = ".") -> str:
    """Search file contents for *pattern* (extended regex / plain substring)."""
    try:
        if shutil.which("rg"):
            cmd = [
                "rg",
                "--line-number",
                "--no-heading",
                "--color",
                "never",
                "--hidden",
                "--glob",
                "!.git/**",
                *[item for d in _EXCLUDE_DIRS for item in ("--glob", f"!{d}/**")],
                "--",
                pattern,
                path,
            ]
        else:
            cmd = [
                "grep",
                "-rnE",  # extended regex so | and () work as models expect
                "--binary-files=without-match",
                *[item for d in _EXCLUDE_DIRS for item in ("--exclude-dir", d)],
                "--",
                pattern,
                path,
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = result.stdout[:4000]
        if out:
            return out
        if result.returncode not in (0, 1):
            err = (result.stderr or "").strip()
            return f"ERROR: search failed (exit {result.returncode}): {err or 'unknown'}"
        return "(no matches)"
    except Exception as e:
        return f"ERROR: {e}"


def build_search_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="search_code",
            description=(
                "Search file contents recursively for a pattern (extended regex). "
                "To find a function or symbol, search for its name "
                '(e.g. read_file or "def read_file"), not unrelated APIs. '
                "Prefer a simple literal; call this tool multiple times for multiple symbols."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Extended regex or plain substring to find",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search (default: .)",
                    },
                },
                "required": ["pattern"],
            },
            executor=lambda **kw: search_code(**kw),
        ),
    ]
