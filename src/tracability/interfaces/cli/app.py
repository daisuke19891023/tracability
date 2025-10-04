"""CLI application factory for the tracability package."""

from __future__ import annotations

import typer

from tracability.interfaces.cli.commands import add_trace_command


def create_app() -> typer.Typer:
    """Construct a Typer application with the trace command registered."""

    application = typer.Typer(
        name="tracability",
        help="Traceability graph query tool",
        add_completion=False,
    )
    add_trace_command(application)
    return application
