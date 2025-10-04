"""Unit tests for application-layer TraceabilityService."""

from __future__ import annotations

from collections.abc import Sequence
import pytest

from tracability import Level, TraceGraph
from tracability.application.service import TraceabilityService
from tracability.domain import TraceResult
from tracability.domain.models import Node
from tracability.infrastructure import LoadOptions


def test_from_files_invokes_loader_with_expected_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """from_files should call loader with provided paths and options."""
    captured: dict[str, object] = {}

    def fake_load_graph(
        relations_csv: str,
        *,
        screens_csv: str | None = None,
        reports_csv: str | None = None,
        tables_csv: str | None = None,
        options: LoadOptions | None = None,
    ) -> TraceGraph:
        assert relations_csv == "relations.csv"
        assert screens_csv == "screens.csv"
        assert reports_csv == "reports.csv"
        assert tables_csv == "tables.csv"
        assert options is not None
        assert options.encoding == "cp932"
        assert options.delimiter == ";"
        graph = TraceGraph()
        captured["graph"] = graph
        return graph

    # Patch the loader symbol used inside the service module
    monkeypatch.setattr(
        "tracability.application.service.load_graph",
        fake_load_graph,
        raising=True,
    )

    svc = TraceabilityService.from_files(
        relations_csv="relations.csv",
        screens_csv="screens.csv",
        reports_csv="reports.csv",
        tables_csv="tables.csv",
        encoding="cp932",
        delimiter=";",
    )

    assert isinstance(svc, TraceabilityService)
    assert getattr(svc, "graph") is captured["graph"]


def test_query_converts_levels_and_delegates_and_formats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """query should convert levels, delegate to graph.trace, and format results."""
    calls: list[dict[str, object]] = []
    last: dict[str, object] = {}

    class DummyGraph(TraceGraph):
        def __init__(self) -> None:  # pragma: no cover - trivial
            super().__init__()

        def trace(
            self,
            from_level: Level,
            to_level: Level,
            target: str,
            *,
            by: str = "auto",
            include_path: bool = False,
            relations: set[str] | None = None,
            direction: str = "both",
            max_depth: int = 16,
        ) -> list[TraceResult]:
            kwargs: dict[str, object] = {
                "from_level": from_level,
                "to_level": to_level,
                "target": target,
                "by": by,
                "include_path": include_path,
                "relations": relations,
                "direction": direction,
                "max_depth": max_depth,
            }
            calls.append(kwargs)
            result = [
                TraceResult(node=Node(level=to_level, id="X"), crud=None, path=[])
            ]
            last["results"] = result
            return result

    formatted_sentinel = {"ok": True}

    def fake_format_results(
        results: Sequence[TraceResult], *, fmt: str, include_path: bool
    ) -> object:
        # Validate the service passed through the results and flags correctly
        assert results is last["results"]
        assert fmt == "list"
        assert include_path is True
        return formatted_sentinel

    # Patch the formatter symbol used inside the service module
    monkeypatch.setattr(
        "tracability.application.service.format_results",
        fake_format_results,
        raising=True,
    )

    svc = TraceabilityService(graph=DummyGraph())

    out = svc.query(
        "program",
        "screen",
        "PG1",
        by="auto",
        include_path=True,
        fmt="list",
        max_depth=8,
        direction="forward",
    )

    assert out is formatted_sentinel
    assert len(calls) == 1
    kwargs = calls[0]

    assert kwargs["from_level"] == Level.PROGRAM
    assert kwargs["to_level"] == Level.SCREEN
    assert kwargs["target"] == "PG1"
    assert kwargs["by"] == "auto"
    assert kwargs["include_path"] is True
    assert kwargs["direction"] == "forward"
    assert kwargs["max_depth"] == 8
    # Default relations if not provided
    assert kwargs["relations"] == {"hierarchy", "screen", "report", "crud"}


def test_query_accepts_level_enums_and_custom_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """query should accept Level enums and forward custom relations set."""
    calls: list[dict[str, object]] = []

    class DummyGraph(TraceGraph):
        def __init__(self) -> None:  # pragma: no cover - trivial
            super().__init__()

        def trace(
            self,
            from_level: Level,
            to_level: Level,
            target: str,
            *,
            by: str = "auto",
            include_path: bool = False,
            relations: set[str] | None = None,
            direction: str = "both",
            max_depth: int = 16,
        ) -> list[TraceResult]:
            kwargs: dict[str, object] = {
                "from_level": from_level,
                "to_level": to_level,
                "target": target,
                "by": by,
                "include_path": include_path,
                "relations": relations,
                "direction": direction,
                "max_depth": max_depth,
            }
            calls.append(kwargs)
            return [TraceResult(node=Node(level=to_level, id="Y"), crud=None, path=[])]

    def fake_format_results(
        results: Sequence[TraceResult], *, fmt: str, include_path: bool
    ) -> object:
        assert fmt == "json"
        assert include_path is False
        return "FORMATTED"

    monkeypatch.setattr(
        "tracability.application.service.format_results",
        fake_format_results,
        raising=True,
    )

    svc = TraceabilityService(graph=DummyGraph())

    out = svc.query(
        Level.PROGRAM,
        Level.TABLE,
        "PG1",
        relations={"crud"},
        fmt="json",
        include_path=False,
    )

    assert out == "FORMATTED"
    assert len(calls) == 1
    kwargs = calls[0]

    assert kwargs["from_level"] == Level.PROGRAM
    assert kwargs["to_level"] == Level.TABLE
    assert kwargs["relations"] == {"crud"}
