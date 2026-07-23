import json

from rich.console import Console

from coding_agent.debug import DebugTracer, dump_json


def test_dump_json_round_trips_messages() -> None:
    payload = {
        "messages": [
            {"role": "system", "content": "hi"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "1",
                        "type": "function",
                        "function": {"name": "list_dir", "arguments": "{}"},
                    }
                ],
            },
        ]
    }
    text = dump_json(payload)
    assert json.loads(text)["messages"][1]["tool_calls"][0]["function"]["name"] == "list_dir"


def test_debug_tracer_noop_when_disabled() -> None:
    console = Console(record=True, force_terminal=True)
    tracer = DebugTracer(console, enabled=False)
    tracer.request(
        model="m",
        messages=[{"role": "user", "content": "x"}],
        tools=[],
        tool_choice="auto",
        iteration=1,
    )
    assert console.export_text() == ""


def test_debug_tracer_prints_when_enabled() -> None:
    console = Console(record=True, force_terminal=True)
    tracer = DebugTracer(console, enabled=True)
    tracer.request(
        model="m",
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"type": "function", "function": {"name": "list_dir"}}],
        tool_choice="auto",
        iteration=1,
    )
    text = console.export_text()
    assert "debug" in text.lower() or "request" in text.lower()
    assert "hello" in text
