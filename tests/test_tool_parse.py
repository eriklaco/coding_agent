import json

from coding_agent.tool_parse import (
    extract_tool_calls_from_text,
    looks_like_deferred_tool_use,
)

KNOWN = {"list_dir", "read_file", "run_shell", "search_code"}


def test_extract_fenced_json_tool_call() -> None:
    content = """To list files I'll call list_dir:

```json
{"name": "list_dir", "arguments": {"path": "."}}
```
"""
    calls = extract_tool_calls_from_text(content, known_tools=KNOWN)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "list_dir"
    assert json.loads(calls[0]["function"]["arguments"]) == {"path": "."}


def test_extract_fenced_nested_arguments() -> None:
    """Non-greedy regex used to truncate nested args at the first '}'."""
    content = """
```json
{"name": "search_code", "arguments": {"path": ".", "pattern": "read_file"}}
```
"""
    calls = extract_tool_calls_from_text(content, known_tools=KNOWN)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "search_code"
    assert json.loads(calls[0]["function"]["arguments"]) == {
        "path": ".",
        "pattern": "read_file",
    }


def test_extract_bare_object() -> None:
    content = 'I will call {"name": "list_dir", "arguments": {"path": "."}} now.'
    calls = extract_tool_calls_from_text(content, known_tools=KNOWN)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "list_dir"


def test_ignores_unknown_tools() -> None:
    content = '{"name": "delete_everything", "arguments": {}}'
    assert extract_tool_calls_from_text(content, known_tools=KNOWN) == []


def test_dedupes_identical_calls() -> None:
    content = """
```json
{"name": "list_dir", "arguments": {"path": "."}}
```
{"name": "list_dir", "arguments": {"path": "."}}
"""
    calls = extract_tool_calls_from_text(content, known_tools=KNOWN)
    assert len(calls) == 1


def test_looks_like_deferred_tool_use() -> None:
    assert looks_like_deferred_tool_use(
        "I'll search for the function responsible for reading files in the src directory."
    )
    assert looks_like_deferred_tool_use("Let me read the config file next.")
    assert not looks_like_deferred_tool_use(
        "The function is named read_file and lives in filesystem.py."
    )
