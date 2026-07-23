from coding_agent.history import trim_history


def test_trim_history_keeps_system_and_tail() -> None:
    messages = [{"role": "system", "content": "sys"}]
    for i in range(10):
        messages.append({"role": "user", "content": f"u{i}"})
        messages.append({"role": "assistant", "content": f"a{i}"})

    trimmed = trim_history(messages, max_messages=5)
    assert len(trimmed) == 5
    assert trimmed[0]["role"] == "system"
    assert trimmed[0]["content"] == "sys"
    assert trimmed[-1]["content"] == "a9"


def test_trim_history_noop_when_under_limit() -> None:
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ]
    assert trim_history(messages, max_messages=40) == messages
