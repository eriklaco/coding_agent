from pathlib import Path

from coding_agent.tools.search import search_code


def test_search_finds_config_constant(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "config.py").write_text('MAX_TOOL_ITERATIONS = 12\nDEFAULT_MODEL = "x"\n')
    monkeypatch.chdir(root)

    out = search_code("MAX_TOOL_ITERATIONS")
    assert "MAX_TOOL_ITERATIONS = 12" in out
    assert "(no matches)" not in out


def test_search_or_pattern_works(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "config.py").write_text('MAX_TOOL_ITERATIONS = 12\nDEFAULT_MODEL = "x"\n')
    monkeypatch.chdir(root)

    out = search_code("MAX_TOOL_ITERATIONS|DEFAULT_MODEL")
    assert "MAX_TOOL_ITERATIONS" in out
    assert "DEFAULT_MODEL" in out


def test_search_skips_cache_dirs(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    cache = root / ".mypy_cache"
    cache.mkdir()
    (root / "src" / "ok.py").write_text("FINDME = 1\n")
    (cache / "noise.py").write_text("FINDME = 2\n")
    monkeypatch.chdir(root)

    out = search_code("FINDME")
    assert "src/ok.py" in out or "ok.py" in out
    assert ".mypy_cache" not in out
