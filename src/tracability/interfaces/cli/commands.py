"""Typer command registration for the tracability CLI interface."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path  # noqa: TC003
from typing import Annotated, Literal, cast

import typer

from tracability.application import TraceabilityService

DEFAULT_RELATIONS: frozenset[str] = frozenset({"hierarchy", "screen", "report", "crud"})


Printer = Callable[[str], None]


def _normalise_relations(value: str | None) -> set[str]:
    """Convert a comma separated relations string into a set."""
    if not value:
        return set(DEFAULT_RELATIONS)
    parsed = {item.strip().lower() for item in value.split(",") if item.strip()}
    return parsed or set(DEFAULT_RELATIONS)


def _render_output(payload: object, fmt: Literal["string", "list", "json"]) -> str:
    """Serialise command output based on the requested format."""
    if fmt == "list":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if fmt == "json":
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return str(payload)


def add_trace_command(
    app: typer.Typer,
    *,
    printer: Printer | None = None,
    error_printer: Printer | None = None,
) -> None:
    """Register the ``trace`` command on the provided Typer application."""
    output: Printer = printer or cast(Printer, typer.echo)

    def _default_error_printer(message: str) -> None:
        typer.echo(message, err=True)

    err_output: Printer = error_printer or _default_error_printer

    def _trace_command(
        relations: Annotated[
            Path,
            typer.Option(
                "--relations",
                "-r",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                help="Path to relations.csv (required)",
            ),
        ],
        from_level: Annotated[
            str,
            typer.Option("--from-level", "-f", help="Start level for the traversal"),
        ],
        to_level: Annotated[
            str,
            typer.Option("--to-level", "-t", help="Target level for the traversal"),
        ],
        target: Annotated[str, typer.Option("--target", help="ID or name to resolve")],
        by: Annotated[
            Literal["auto", "id", "name"],
            typer.Option(
                "--by",
                help="Interpretation mode for target",
                case_sensitive=False,
                show_default=True,
            ),
        ] = "auto",
        screens: Annotated[
            Path | None,
            typer.Option(
                "--screens",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                help="Optional screens master CSV",
            ),
        ] = None,
        reports: Annotated[
            Path | None,
            typer.Option(
                "--reports",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                help="Optional reports master CSV",
            ),
        ] = None,
        tables: Annotated[
            Path | None,
            typer.Option(
                "--tables",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                help="Optional tables master CSV",
            ),
        ] = None,
        relations_filter: Annotated[
            str | None,
            typer.Option(
                "--relations-filter",
                help="Comma separated relation list (defaults to all)",
            ),
        ] = None,
        include_path: Annotated[
            bool,
            typer.Option(
                "--include-path",
                help="Return traversed edges",
                show_default=True,
            ),
        ] = False,
        fmt: Annotated[
            Literal["string", "list", "json"],
            typer.Option(
                "--format",
                "-m",
                help="Output format",
                case_sensitive=False,
                show_default=True,
            ),
        ] = "string",
        encoding: Annotated[
            str,
            typer.Option("--encoding", help="CSV encoding", show_default=True),
        ] = "utf-8-sig",
        delimiter: Annotated[
            str,
            typer.Option("--delimiter", help="CSV delimiter", show_default=True),
        ] = ",",
        max_depth: Annotated[
            int,
            typer.Option("--max-depth", help="Maximum BFS depth", show_default=True),
        ] = 16,
    ) -> None:
        """Execute a traceability graph query based on CSV inputs."""
        try:
            service = TraceabilityService.from_files(
                str(relations),
                screens_csv=str(screens) if screens else None,
                reports_csv=str(reports) if reports else None,
                tables_csv=str(tables) if tables else None,
                encoding=encoding,
                delimiter=delimiter,
            )
            relation_set = _normalise_relations(relations_filter)
            results = service.query(
                from_level,
                to_level,
                target,
                by=by,
                relations=relation_set,
                include_path=include_path,
                fmt=fmt,
                max_depth=max_depth,
            )
            output(_render_output(results, fmt))
        except Exception as exc:
            err_output(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

    app.command("trace")(_trace_command)

