"""Recover tool calls when a model emits them as text instead of tool_calls."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from openai.types.chat.chat_completion_message_function_tool_call_param import (
    ChatCompletionMessageFunctionToolCallParam,
)

_FENCE = re.compile(r"```(?:json|JSON)?\s*\n?(.*?)\n?\s*```", re.DOTALL)


def _extract_balanced_object(text: str, start: int) -> str | None:
    """Return the JSON object starting at text[start] == '{', or None."""
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_string = False
    escape = False
    for j in range(start, len(text)):
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
                return text[start : j + 1]
    return None


def _iter_json_objects(text: str) -> list[str]:
    """Extract top-level `{...}` slices with string-aware brace matching."""
    objects: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "{":
            i += 1
            continue
        obj = _extract_balanced_object(text, i)
        if obj is None:
            break
        objects.append(obj)
        i += len(obj)
    return objects


def _candidates_from_text(content: str) -> list[str]:
    """Collect possible JSON tool-call payloads from fenced blocks and raw objects."""
    candidates: list[str] = []
    for fence_body in _FENCE.findall(content):
        body = fence_body.strip()
        if body.startswith("{"):
            obj = _extract_balanced_object(body, 0)
            if obj:
                candidates.append(obj)
            else:
                candidates.append(body)
        candidates.extend(_iter_json_objects(body))
    candidates.extend(_iter_json_objects(content))
    return candidates


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

    seen: set[str] = set()
    calls: list[ChatCompletionMessageFunctionToolCallParam] = []
    for raw in _candidates_from_text(content):
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


_INTENDED_TOOL_USE = re.compile(
    r"(?is)\b("
    r"i(?:'ll| will)|let me|i am going to|next i(?:'ll| will)|"
    r"we(?:'ll| will)|going to"
    r")\b.{0,100}\b("
    r"search|read|list|look|find|call|check|open|use|run|inspect|grep"
    r")\b"
)


def looks_like_deferred_tool_use(content: str) -> bool:
    """True when the model narrates a tool step instead of calling it."""
    text = content.strip()
    if not text:
        return False
    return bool(_INTENDED_TOOL_USE.search(text))
