from coding_agent.cli import _is_noise_input


def test_noise_input_detects_empty_and_ansi() -> None:
    assert _is_noise_input("")
    assert _is_noise_input("   ")
    assert _is_noise_input("\x1b[A")
    assert _is_noise_input("^[[A")
    assert not _is_noise_input("find read_file")
