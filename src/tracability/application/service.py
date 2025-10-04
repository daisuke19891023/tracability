"""Application service orchestrating traceability queries."""

from __future__ import annotations

from typing import Literal, overload

from tracability.domain import Level, TraceGraph
from tracability.infrastructure import LoadOptions, load_graph
from tracability.interfaces.formatter import ListResult, format_results

OutputFormat = Literal["string", "list", "json"]
TraceOutput = str | list[ListResult]


class TraceabilityService:
    """High-level API for querying traceability relationships."""

    def __init__(self, graph: TraceGraph) -> None:
        """Create a service backed by the provided graph."""

        self.graph = graph

    @classmethod
    def from_files(
        cls,
        relations_csv: str,
        *,
        screens_csv: str | None = None,
        reports_csv: str | None = None,
        tables_csv: str | None = None,
        encoding: str = "utf-8-sig",
        delimiter: str = ",",
    ) -> "TraceabilityService":
        """Build a service by loading CSV resources from disk."""

        graph = load_graph(
            relations_csv,
            screens_csv=screens_csv,
            reports_csv=reports_csv,
            tables_csv=tables_csv,
            options=LoadOptions(encoding=encoding, delimiter=delimiter),
        )
        return cls(graph)

    @overload
    def query(
        self,
        from_level: str | Level,
        to_level: str | Level,
        target: str,
        *,
        by: str = "auto",
        relations: set[str] | None = None,
        include_path: bool = False,
        fmt: Literal["list"],
        max_depth: int = 16,
        direction: str = "both",
    ) -> list[ListResult]:
        ...

    @overload
    def query(
        self,
        from_level: str | Level,
        to_level: str | Level,
        target: str,
        *,
        by: str = "auto",
        relations: set[str] | None = None,
        include_path: bool = False,
        fmt: Literal["string"],
        max_depth: int = 16,
        direction: str = "both",
    ) -> str:
        ...

    @overload
    def query(
        self,
        from_level: str | Level,
        to_level: str | Level,
        target: str,
        *,
        by: str = "auto",
        relations: set[str] | None = None,
        include_path: bool = False,
        fmt: Literal["json"],
        max_depth: int = 16,
        direction: str = "both",
    ) -> str:
        ...

    def query(
        self,
        from_level: str | Level,
        to_level: str | Level,
        target: str,
        *,
        by: str = "auto",
        relations: set[str] | None = None,
        include_path: bool = False,
        fmt: OutputFormat = "list",
        max_depth: int = 16,
        direction: str = "both",
    ) -> TraceOutput:
        """Execute a trace query and format the results."""

        from_lvl = from_level if isinstance(from_level, Level) else Level.parse(from_level)
        to_lvl = to_level if isinstance(to_level, Level) else Level.parse(to_level)
        rels = relations or {"hierarchy", "screen", "report", "crud"}
        results = self.graph.trace(
            from_level=from_lvl,
            to_level=to_lvl,
            target=target,
            by=by,
            include_path=include_path,
            relations=rels,
            direction=direction,
            max_depth=max_depth,
        )
        return format_results(results, fmt=fmt, include_path=include_path)
