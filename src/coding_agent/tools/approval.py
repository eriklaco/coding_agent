"""Interactive Rich-backed approval gate (and a no-op yolo gate)."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax


class RichApprovalGate:
    """Prompt for confirmation on writes/edits/shell via Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def confirm(self, prompt: str) -> bool:
        return Confirm.ask(prompt, console=self.console)

    def show_diff(self, path: str, diff: str) -> None:
        self.console.print(
            Panel(Syntax(diff, "diff", theme="ansi_dark"), title=f"Proposed edit: {path}")
        )

    def notify(self, message: str) -> None:
        self.console.print(f"[yellow]{message}[/yellow]")


class YoloApprovalGate:
    """Always approve; used with --yolo."""

    def confirm(self, prompt: str) -> bool:
        return True

    def show_diff(self, path: str, diff: str) -> None:
        return None

    def notify(self, message: str) -> None:
        return None
