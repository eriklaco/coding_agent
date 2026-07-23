"""Compact terminal UI for tool calls (collapsed one-liners + short results)."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


def format_elapsed(seconds: float) -> str:
    """Human-readable duration, e.g. 4.2s or 1m 03s."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rem = divmod(seconds, 60)
    return f"{int(minutes)}m {rem:04.1f}s"


def _format_args(args: dict[str, Any], *, max_len: int = 80) -> str:
    parts: list[str] = []
    for key, value in args.items():
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if len(rendered) > 40:
            rendered = rendered[:37] + "..."
        parts.append(f"{key}={rendered!r}" if isinstance(value, str) else f"{key}={rendered}")
    joined = " ".join(parts)
    if len(joined) > max_len:
        return joined[: max_len - 3] + "..."
    return joined


def _preview_result(result: str, *, max_lines: int = 4, max_chars: int = 240) -> str:
    text = result.strip()
    if not text:
        return "(empty)"
    lines = text.splitlines()
    clipped = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        clipped += f"\n… ({len(lines) - max_lines} more lines)"
    if len(clipped) > max_chars:
        clipped = clipped[: max_chars - 1] + "…"
    return clipped


class _ElapsedTicker:
    """Live-updating 'thinking… Ns' line (elapsed since the user prompt)."""

    def __init__(self, start: float, label: str) -> None:
        self.start = start
        self.label = label

    def __rich__(self) -> RenderableType:
        elapsed = time.perf_counter() - self.start
        return Text.assemble(
            ("… ", "cyan"),
            (f"{self.label}  ", "dim"),
            (format_elapsed(elapsed), "bold dim"),
        )


class TurnClock:
    """Wall-clock for one agent turn: live counter while waiting, total at the end."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._start = 0.0
        self.last_elapsed = 0.0

    def start(self) -> None:
        self._start = time.perf_counter()
        self.last_elapsed = 0.0

    def stop(self) -> float:
        self.last_elapsed = time.perf_counter() - self._start
        return self.last_elapsed

    @contextmanager
    def waiting(self, label: str = "thinking") -> Iterator[None]:
        """Show a live second counter while blocked (e.g. on the model)."""
        ticker = _ElapsedTicker(self._start, label)
        with Live(
            ticker,
            console=self.console,
            refresh_per_second=8,
            transient=True,
        ):
            yield


class ToolTracer:
    """Prints tool activity as a small collapsed panel (name + args + result preview)."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def tool_start(self, name: str, args: dict[str, Any]) -> None:
        header = Text.assemble(
            ("⚙ ", "bold cyan"),
            (name, "bold"),
            ("  ", ""),
            (_format_args(args), "dim"),
        )
        self.console.print(header)

    def tool_end(self, name: str, result: str) -> None:
        preview = _preview_result(result)
        is_error = result.startswith("ERROR:") or result == "DENIED by user"
        border = "red" if is_error else "dim"
        self.console.print(
            Panel(
                Group(Text(preview, style="dim" if not is_error else "red")),
                title=f"[dim]{name}[/dim]",
                border_style=border,
                expand=False,
                padding=(0, 1),
            )
        )
