"""Typer CLI for the coding agent."""

from __future__ import annotations

import typer
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from coding_agent.agent import Agent
from coding_agent.config import DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_MODEL
from coding_agent.tools.approval import RichApprovalGate, YoloApprovalGate
from coding_agent.ui import format_elapsed

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """Minimal Claude-Code-style coding agent CLI."""


@app.command()
def chat(
    model: str = typer.Option(DEFAULT_MODEL, help="Model name as known to your local server"),
    base_url: str = typer.Option(DEFAULT_BASE_URL, help="OpenAI-compatible endpoint"),
    api_key: str = typer.Option(DEFAULT_API_KEY, help="API key; most local servers ignore it"),
    yolo: bool = typer.Option(False, "--yolo", help="Skip confirmation prompts (dangerous)"),
) -> None:
    """Start an interactive coding-agent session in the current directory."""
    client = OpenAI(base_url=base_url, api_key=api_key)
    gate = YoloApprovalGate() if yolo else RichApprovalGate(console)
    agent = Agent(client, model, gate, console=console)

    console.print(
        Panel.fit(
            f"coding-agent · model=[bold]{model}[/bold] · endpoint={base_url}"
            + (
                "\n[bold red]--yolo enabled: writes/edits/shell run without confirmation[/bold red]"
                if yolo
                else ""
            ),
            title="ready",
        )
    )

    while True:
        try:
            user_input = console.input("[bold cyan]you>[/bold cyan] ")
        except EOFError, KeyboardInterrupt:
            console.print("\nbye")
            break
        if not user_input.strip():
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
                reply,
                title="agent",
                subtitle=f"[dim]⏱ {elapsed}[/dim]",
                border_style="green",
            )
        )


if __name__ == "__main__":
    app()
