"""Recover tool calls when a model emits them as text instead of tool_calls."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from openai.types.chat.chat_completion_message_function_tool_call_param import (
    ChatCompletionMessageFunctionToolCallParam,
)

_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _iter_json_objects(text: str) -> list[str]:
    """Extract top-level `{...}` slices with naive string-aware brace matching."""
    objects: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        in_string = False
        escape = False
        start = i
        for j in range(i, len(text)):
            ch = text[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    objects.append(text[start : j + 1])
                    i = j + 1
                    break
        else:
            break
    return objects


def _normalize_call(payload: dict[str, Any]) -> ChatCompletionMessageFunctionToolCallParam | None:
    name: str | None = None
    arguments: Any = {}

    if "name" in payload and ("arguments" in payload or "parameters" in payload):
        name = str(payload["name"])
        arguments = payload.get("arguments", payload.get("parameters", {}))
    elif isinstance(payload.get("function"), dict):
        fn = payload["function"]
        name = str(fn.get("name", ""))
        arguments = fn.get("arguments", fn.get("parameters", {}))

    if not name:
        return None

    if isinstance(arguments, str):
        args_json = arguments
    else:
        args_json = json.dumps(arguments if isinstance(arguments, dict) else {})

    return {
        "id": f"fallback_{uuid.uuid4().hex[:12]}",
        "type": "function",
        "function": {"name": name, "arguments": args_json},
    }


def extract_tool_calls_from_text(
    content: str,
    *,
    known_tools: set[str],
) -> list[ChatCompletionMessageFunctionToolCallParam]:
    """Parse tool-call JSON from assistant text when native tool_calls are missing."""
    if not content.strip():
        return []

    candidates: list[str] = []
    candidates.extend(_FENCED_JSON.findall(content))
    candidates.extend(_iter_json_objects(content))

    seen: set[str] = set()
    calls: list[ChatCompletionMessageFunctionToolCallParam] = []
    for raw in candidates:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        call = _normalize_call(payload)
        if call is None:
            continue
        name = call["function"]["name"]
        if name not in known_tools:
            continue
        key = f"{name}:{call['function']['arguments']}"
        if key in seen:
            continue
        seen.add(key)
        calls.append(call)
    return calls
