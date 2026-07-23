from coding_agent.ui import format_elapsed


def test_format_elapsed_seconds() -> None:
    assert format_elapsed(4.2) == "4.2s"
    assert format_elapsed(0.05) == "0.1s" or format_elapsed(0.05) == "0.0s"


def test_format_elapsed_minutes() -> None:
    assert format_elapsed(65.2) == "1m 05.2s"
