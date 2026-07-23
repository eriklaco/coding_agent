"""Default tool set: schemas + executors built from ToolSpecs."""

from __future__ import annotations

from collections.abc import Callable

from openai.types.chat import ChatCompletionToolParam

from coding_agent.tools.base import (
    ApprovalGate,
    ToolSpec,
    executors_from_tools,
    schemas_from_tools,
)
from coding_agent.tools.filesystem import build_filesystem_tools
from coding_agent.tools.search import build_search_tools
from coding_agent.tools.shell import build_shell_tools


def build_default_tools(gate: ApprovalGate) -> list[ToolSpec]:
    return [
        *build_filesystem_tools(gate),
        *build_search_tools(),
        *build_shell_tools(gate),
    ]


def make_tool_bundle(
    gate: ApprovalGate,
) -> tuple[list[ChatCompletionToolParam], dict[str, Callable[..., str]]]:
    """Return (openai_tool_schemas, name→executor) for the default tool set."""
    tools = build_default_tools(gate)
    return schemas_from_tools(tools), executors_from_tools(tools)
