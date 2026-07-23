"""Filesystem tools: read, list, write, edit."""

from __future__ import annotations

import difflib
from pathlib import Path

from coding_agent.tools.base import ApprovalGate, ToolSpec


def read_file(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    lines = p.read_text(errors="replace").splitlines()
    if start_line or end_line:
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        lines = lines[s:e]
        offset = s
    else:
        offset = 0
    return "\n".join(f"{offset + i + 1:>5}\t{line}" for i, line in enumerate(lines))


def list_dir(path: str = ".") -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    return "\n".join(f"{'[dir] ' if e.is_dir() else '      '}{e.name}" for e in entries)


def write_file(path: str, content: str, gate: ApprovalGate) -> str:
    p = Path(path)
    if p.exists():
        gate.notify(f"Model wants to overwrite existing file: {path}")
        if not gate.confirm("Allow?"):
            return "DENIED by user"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"OK: wrote {len(content)} bytes to {path}"


def edit_file(path: str, old_str: str, new_str: str, gate: ApprovalGate) -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    original = p.read_text()
    count = original.count(old_str)
    if count == 0:
        return "ERROR: old_str not found in file (must match exactly, including whitespace)"
    if count > 1:
        return f"ERROR: old_str is not unique ({count} occurrences) — include more context"

    updated = original.replace(old_str, new_str, 1)
    diff = "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=path,
            tofile=path,
            lineterm="",
        )
    )
    gate.show_diff(path, diff)
    if not gate.confirm("Apply this edit?"):
        return "DENIED by user"

    p.write_text(updated)
    return f"OK: edited {path}"


def build_filesystem_tools(gate: ApprovalGate) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="read_file",
            description=(
                "Read a file's contents, optionally a line range. Always do this before editing."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                },
                "required": ["path"],
            },
            executor=lambda **kw: read_file(**kw),
        ),
        ToolSpec(
            name="list_dir",
            description="List files and directories at a path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
            executor=lambda **kw: list_dir(**kw),
        ),
        ToolSpec(
            name="write_file",
            description=(
                "Create a new file or fully overwrite an existing one. "
                "Prefer edit_file for existing files."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            executor=lambda **kw: write_file(gate=gate, **kw),
        ),
        ToolSpec(
            name="edit_file",
            description=(
                "Replace an exact, unique snippet of text in an existing file (find-and-replace)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {
                        "type": "string",
                        "description": "Exact text to find, must be unique in the file",
                    },
                    "new_str": {
                        "type": "string",
                        "description": "Text to replace it with",
                    },
                },
                "required": ["path", "old_str", "new_str"],
            },
            executor=lambda **kw: edit_file(gate=gate, **kw),
        ),
    ]
