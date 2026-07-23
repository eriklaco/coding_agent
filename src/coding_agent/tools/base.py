"""Tool registry primitives and approval gate protocol."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from openai.types.chat import ChatCompletionToolParam


class ApprovalGate(Protocol):
    """Permission layer for state-changing tools.

    Implementations can prompt the user, auto-approve (yolo), or enforce
    policy in a sandbox later.
    """

    def confirm(self, prompt: str) -> bool:
        """Return True if the action is allowed."""
        ...

    def show_diff(self, path: str, diff: str) -> None:
        """Display a proposed edit before confirmation."""
        ...

    def notify(self, message: str) -> None:
        """Print a non-blocking notice (e.g. pending shell command)."""
        ...


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """One tool: OpenAI schema fields + Python executor."""

    name: str
    description: str
    parameters: dict[str, Any]
    executor: Callable[..., str]

    def openai_schema(self) -> ChatCompletionToolParam:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def schemas_from_tools(tools: list[ToolSpec]) -> list[ChatCompletionToolParam]:
    return [t.openai_schema() for t in tools]


def executors_from_tools(tools: list[ToolSpec]) -> dict[str, Callable[..., str]]:
    return {t.name: t.executor for t in tools}
