"""Command line entry point delegating to the CLI interface package."""

from __future__ import annotations

from tracability.interfaces.cli.app import create_app


app = create_app()


def main() -> None:
    """Execute the tracability CLI application."""
    app()


if __name__ == "__main__":  # pragma: no cover - CLI module execution guard
    main()
