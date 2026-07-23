import json

from coding_agent.tool_parse import extract_tool_calls_from_text

KNOWN = {"list_dir", "read_file", "run_shell"}


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
