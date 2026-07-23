"""Typer CLI for the coding agent."""

from __future__ import annotations

import re

import typer
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from coding_agent.agent import Agent
from coding_agent.config import DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_MODEL
from coding_agent.repl import read_user_line
from coding_agent.tools.approval import RichApprovalGate, YoloApprovalGate
from coding_agent.ui import format_elapsed

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

# Arrow keys / other CSI sequences that leak into input on some terminals.
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\^\[\[[A-Za-z]")


def _is_noise_input(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    cleaned = _ANSI_ESCAPE.sub("", stripped).strip()
    return not cleaned


@app.callback()
def main() -> None:
    """Minimal Claude-Code-style coding agent CLI."""


@app.command()
def chat(
    model: str = typer.Option(DEFAULT_MODEL, help="Model name as known to your local server"),
    base_url: str = typer.Option(DEFAULT_BASE_URL, help="OpenAI-compatible endpoint"),
    api_key: str = typer.Option(DEFAULT_API_KEY, help="API key; most local servers ignore it"),
    yolo: bool = typer.Option(False, "--yolo", help="Skip confirmation prompts (dangerous)"),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Dump full request/response context (messages, tools, tool_calls) each model call",
    ),
) -> None:
    """Start an interactive coding-agent session in the current directory."""
    client = OpenAI(base_url=base_url, api_key=api_key)
    gate = YoloApprovalGate() if yolo else RichApprovalGate(console)
    agent = Agent(client, model, gate, console=console, debug=debug)

    console.print(
        Panel.fit(
            f"coding-agent · model=[bold]{model}[/bold] · endpoint={base_url}"
            + (
                "\n[bold red]--yolo enabled: writes/edits/shell run without confirmation[/bold red]"
                if yolo
                else ""
            )
            + (
                "\n[magenta]--debug enabled: dumping model I/O each call[/magenta]" if debug else ""
            ),
            title="ready",
        )
    )

    while True:
        try:
            user_input = read_user_line(console)
        except EOFError, KeyboardInterrupt:
            console.print("\nbye")
            break
        if _is_noise_input(user_input):
            continue
        if user_input.strip() in ("/exit", "/quit"):
            break

        try:
            reply = agent.run_turn(user_input)
        except Exception as e:
            console.print(f"[red]error talking to model:[/red] {e}")
            continue

        elapsed = format_elapsed(agent.last_turn_elapsed)
        console.print(
            Panel(
                Markdown(reply or ""),
                title="agent",
                subtitle=f"[dim]⏱ {elapsed}[/dim]",
                border_style="green",
            )
        )


if __name__ == "__main__":
    app()
