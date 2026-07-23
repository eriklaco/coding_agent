from pathlib import Path

from coding_agent.tools.filesystem import edit_file, list_dir, read_file, write_file


def test_read_file_line_range(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text("a\nb\nc\nd\ne\n")
    out = read_file(str(path), start_line=2, end_line=4)
    assert "    2\tb" in out
    assert "    4\td" in out
    assert "    1\ta" not in out
    assert "    5\te" not in out


def test_read_file_missing() -> None:
    assert read_file("/nonexistent/path/xyz").startswith("ERROR:")


def test_list_dir(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("hi")
    (tmp_path / "subdir").mkdir()
    out = list_dir(str(tmp_path))
    assert "file.txt" in out
    assert "[dir] subdir" in out


def test_edit_file_requires_unique_match(tmp_path: Path, allow_gate) -> None:
    path = tmp_path / "dup.txt"
    path.write_text("foo\nfoo\n")
    result = edit_file(str(path), "foo", "bar", allow_gate)
    assert "not unique" in result
    assert path.read_text() == "foo\nfoo\n"


def test_edit_file_applies_unique_replace(tmp_path: Path, allow_gate) -> None:
    path = tmp_path / "once.txt"
    path.write_text("hello world\n")
    result = edit_file(str(path), "world", "agent", allow_gate)
    assert result.startswith("OK:")
    assert path.read_text() == "hello agent\n"


def test_edit_file_denied(tmp_path: Path, deny_gate) -> None:
    path = tmp_path / "once.txt"
    path.write_text("hello world\n")
    result = edit_file(str(path), "world", "agent", deny_gate)
    assert result == "DENIED by user"
    assert path.read_text() == "hello world\n"


def test_write_file_new(tmp_path: Path, allow_gate) -> None:
    path = tmp_path / "nested" / "new.txt"
    result = write_file(str(path), "content", allow_gate)
    assert result.startswith("OK:")
    assert path.read_text() == "content"
