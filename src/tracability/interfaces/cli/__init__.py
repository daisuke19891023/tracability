"""CLI interface package for tracability."""

from tracability.interfaces.cli.app import create_app
from tracability.interfaces.cli.commands import add_trace_command

__all__ = ["create_app", "add_trace_command"]
