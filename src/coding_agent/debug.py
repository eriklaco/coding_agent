"""Optional debug dumps of model request/response context."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonable(model_dump())
    return str(value)


def dump_json(data: Any, *, indent: int = 2) -> str:
    return json.dumps(_jsonable(data), indent=indent, ensure_ascii=False)


class DebugTracer:
    """Pretty-print outbound prompts and inbound model replies when enabled."""

    def __init__(self, console: Console, *, enabled: bool = False) -> None:
        self.console = console
        self.enabled = enabled

    def request(
        self,
        *,
        model: str,
        messages: list[Any],
        tools: list[Any],
        tool_choice: str,
        iteration: int,
    ) -> None:
        if not self.enabled:
            return
        payload = {
            "iteration": iteration,
            "model": model,
            "tool_choice": tool_choice,
            "message_count": len(messages),
            "messages": messages,
            "tools": tools,
        }
        self.console.print(
            Panel(
                Syntax(dump_json(payload), "json", theme="ansi_dark", word_wrap=True),
                title=f"debug → request (iteration {iteration})",
                border_style="magenta",
            )
        )

    def response(self, *, message: Any, iteration: int, finish_reason: str | None) -> None:
        if not self.enabled:
            return
        tool_calls = getattr(message, "tool_calls", None)
        payload = {
            "iteration": iteration,
            "finish_reason": finish_reason,
            "content": getattr(message, "content", None),
            "tool_calls": tool_calls,
        }
        self.console.print(
            Panel(
                Syntax(dump_json(payload), "json", theme="ansi_dark", word_wrap=True),
                title=f"debug ← response (iteration {iteration})",
                border_style="magenta",
            )
        )
