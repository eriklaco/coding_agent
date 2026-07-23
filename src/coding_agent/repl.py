"""Interactive prompt with up/down arrow command history (readline)."""

from __future__ import annotations

import atexit
import contextlib
from pathlib import Path

from rich.console import Console

_HISTORY_FILE = Path.home() / ".coding_agent_history"
_HISTORY_LENGTH = 1000
_setup_done = False


def _setup_readline() -> None:
    """Enable persistent line editing / history if readline is available."""
    global _setup_done
    if _setup_done:
        return
    _setup_done = True

    try:
        import readline
    except ImportError:
        return

    with contextlib.suppress(OSError):
        readline.read_history_file(_HISTORY_FILE)

    readline.set_history_length(_HISTORY_LENGTH)

    # libedit (macOS) vs GNU readline use different bind syntax.
    doc = getattr(readline, "__doc__", "") or ""
    if "libedit" in doc:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    def _save() -> None:
        with contextlib.suppress(OSError):
            _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(_HISTORY_FILE)

    atexit.register(_save)


def read_user_line(console: Console, prompt: str = "[bold cyan]you>[/bold cyan] ") -> str:
    """Read a line with Rich-styled prompt and shell-like up/down history."""
    _setup_readline()
    console.print(prompt, end="")
    return input()
