"""Utilities for rendering traceability results."""

from __future__ import annotations

import json
import typing as t
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:  # pragma: no cover - typing only
    from tracability.domain.graph import TracePathStep, TraceResult

OutputFormat = Literal["string", "list", "json"]

PathDict = TypedDict(
    "PathDict",
    {"from": str, "relation": str, "to": str},
)


class _BaseListResult(TypedDict):
    level: str
    id: str
    logical_name: str | None
    physical_name: str | None
    crud: list[str] | None


class ListResult(_BaseListResult, total=False):
    """Typed mapping for ``fmt='list'`` responses."""

    path: list[PathDict]


def _format_path_entry(entry: TracePathStep) -> PathDict:
    src, relation, dst = entry
    return {
        "from": f"{src.level.value}:{src.id}",
        "relation": relation,
        "to": f"{dst.level.value}:{dst.id}",
    }


def format_results(
    results: t.Sequence[TraceResult],
    fmt: OutputFormat = "string",
    include_path: bool = False,
) -> str | list[ListResult]:
    """Convert traced nodes into user-facing output formats."""
    if fmt == "list":
        formatted: list[ListResult] = []
        for record in results:
            node = record.node
            entry: ListResult = {
                "level": node.level.value,
                "id": node.id,
                "logical_name": node.logical_name,
                "physical_name": node.physical_name,
                "crud": sorted(record.crud) if record.crud else None,
            }
            if include_path and record.path:
                entry["path"] = [_format_path_entry(step) for step in record.path]
            formatted.append(entry)
        return formatted
    if fmt == "json":
        return json.dumps(
            format_results(results, fmt="list", include_path=include_path),
            ensure_ascii=False,
            indent=2,
        )
    if not results:
        return "一致する結果はありません。"
    lines: list[str] = []
    for index, record in enumerate(results, 1):
        node = record.node
        crud_suffix = f"  CRUD={','.join(sorted(record.crud))}" if record.crud else ""
        lines.append(f"[{index}] {node.level.value}: {node.label()}{crud_suffix}")
        if include_path and record.path:
            for src, relation, dst in record.path:
                relation_text = (
                    f"    {src.level.value}:{src.id} --{relation}--> "
                    f"{dst.level.value}:{dst.id}"
                )
                lines.append(relation_text)
    return "\n".join(lines)
