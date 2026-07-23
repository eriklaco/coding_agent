"""Shell execution tool."""

from __future__ import annotations

import subprocess

from coding_agent.tools.base import ApprovalGate, ToolSpec


def run_shell(command: str, gate: ApprovalGate, timeout: int = 30) -> str:
    gate.notify(f"Model wants to run shell command: {command}")
    if not gate.confirm("Allow?"):
        return "DENIED by user"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = result.stdout[-3000:]
        err = result.stderr[-1500:]
        return f"exit={result.returncode}\nstdout:\n{out}\nstderr:\n{err}"
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"


def build_shell_tools(gate: ApprovalGate) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="run_shell",
            description=(
                "Run a shell command in the project directory and return stdout/stderr/exit code."
            ),
            parameters={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
            executor=lambda **kw: run_shell(gate=gate, **kw),
        ),
    ]
