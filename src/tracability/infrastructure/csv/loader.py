"""CSV loader composing the infrastructure layer of tracability."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import typing as t

from tracability.domain import Level, Node, NodeIndex, TraceGraph
from tracability.shared.utils import nfkc_lower, parse_crud

ALIASES = {
    "subsystem_id": [
        "サブシステムid",
        "サブシステムID",
        "subsystem_id",
        "ss_id",
        "subsystem code",
    ],
    "subsystem_name": [
        "サブシステム名",
        "subsystem_name",
        "subsystem logical name",
        "サブシステム論理名",
    ],
    "business_id": ["業務id", "業務ID", "business_id", "biz_id"],
    "business_name": ["業務名", "business_name", "業務論理名"],
    "function_id": ["機能id", "機能ID", "function_id", "fn_id"],
    "function_name": ["機能名", "function_name", "機能論理名"],
    "program_id": ["プログラムid", "プログラムID", "program_id", "pgm_id", "source_id"],
    "program_name": ["プログラム名", "program_name", "プログラム論理名"],
    "screen_id": ["画面id", "画面ID", "screen_id", "ui_id"],
    "report_id": ["帳票id", "帳票ID", "report_id", "rp_id"],
    "table_id": ["テーブルid", "テーブルID", "table_id", "db_table", "table"],
    "crud": ["crud", "operations", "crud_operations"],
    "logical_name": [
        "論理名",
        "名称",
        "name",
        "logical_name",
        "display_name",
        "ラベル",
    ],
    "physical_name": [
        "物理名",
        "英名",
        "physical_name",
        "table_name",
        "screen_name",
        "report_name",
    ],
    "id": ["id", "コード", "code", "識別子"],
    "master_function_id": ["機能id", "機能ID", "function_id", "fn_id"],
}


def _alias_score(field: str, header: str) -> int:
    score = 0
    for alias in ALIASES.get(field, []):
        normalized_alias = nfkc_lower(alias) or ""
        if header == normalized_alias:
            score += 100
        elif normalized_alias and normalized_alias in header:
            score += 60
    return score


def _id_score(field: str, header: str) -> int:
    score = 0
    if field.endswith("_id") or field in {"id", "master_function_id"}:
        if "id" in header:
            score += 5
        if "code" in header:
            score += 3
    return score


def _name_score(field: str, header: str) -> int:
    score = 0
    if "logical" in field or field.endswith("_name"):
        if "name" in header:
            score += 3
        if "論理" in header:
            score += 4
    return score


def _physical_score(field: str, header: str) -> int:
    if "physical" in field and ("physical" in header or "物理" in header):
        return 5
    return 0


def _match_score(field: str, header: str) -> int:
    return (
        _alias_score(field, header)
        + _id_score(field, header)
        + _name_score(field, header)
        + _physical_score(field, header)
    )


def _resolve_columns(
    headers: t.Sequence[str],
    needed: t.Sequence[str],
) -> dict[str, str | None]:
    normalized: dict[str, str] = {}
    for header in headers:
        if not header:
            continue
        normalized[header] = nfkc_lower(header) or ""
    result: dict[str, str | None] = dict.fromkeys(needed)
    used: set[str] = set()

    for field in needed:
        best_header: str | None = None
        best_score = -1
        for header, lowered in normalized.items():
            if header in used:
                continue
            candidate_score = _match_score(field, lowered)
            if candidate_score > best_score:
                best_header = header
                best_score = candidate_score
        if best_header and best_score > 0:
            result[field] = best_header
            used.add(best_header)
    return result


def _get(row: t.Mapping[str, str | None], col: str | None) -> str | None:
    if not col:
        return None
    target = nfkc_lower(col)
    for key, value in row.items():
        if nfkc_lower(key) == target:
            if value is None:
                return None
            normalized_value = value.strip()
            return normalized_value or None
    return None


def _upsert_optional(
    index: NodeIndex,
    level: Level,
    identifier: str | None,
    logical_name: str | None,
) -> Node | None:
    candidate = identifier or logical_name
    if candidate is None:
        return None
    return index.upsert(level, candidate, logical_name=logical_name)


@dataclass(slots=True)
class LoadOptions:
    """Runtime configuration for CSV parsing."""

    encoding: str = "utf-8-sig"
    delimiter: str = ","


def _load_screen_report_master(
    graph: TraceGraph,
    level: Level,
    csv_path: str | None,
    opts: LoadOptions,
) -> None:
    if not csv_path:
        return
    index = graph.index
    with Path(csv_path).open("r", encoding=opts.encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=opts.delimiter)
        headers = reader.fieldnames or []
        cols = _resolve_columns(
            headers,
            ["id", "logical_name", "physical_name", "master_function_id"],
        )
        for row in reader:
            idv = (
                _get(row, cols["id"])
                or _get(row, cols["physical_name"])
                or _get(row, cols["logical_name"])
            )
            if not idv:
                continue
            logical = _get(row, cols["logical_name"])
            physical = _get(row, cols["physical_name"])
            fn_id = _get(row, cols["master_function_id"])
            node = index.upsert(
                level,
                idv,
                logical_name=logical,
                physical_name=physical,
            )
            if fn_id:
                fn = index.upsert(Level.FUNCTION, fn_id)
                if level == Level.SCREEN:
                    graph.add_screen(fn, node)
                else:
                    graph.add_report(fn, node)


def _load_table_master(
    graph: TraceGraph,
    csv_path: str | None,
    opts: LoadOptions,
) -> None:
    if not csv_path:
        return
    index = graph.index
    with Path(csv_path).open("r", encoding=opts.encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=opts.delimiter)
        headers = reader.fieldnames or []
        cols = _resolve_columns(headers, ["id", "logical_name", "physical_name"])
        for row in reader:
            idv = (
                _get(row, cols["id"])
                or _get(row, cols["physical_name"])
                or _get(row, cols["logical_name"])
            )
            if not idv:
                continue
            logical = _get(row, cols["logical_name"])
            physical = _get(row, cols["physical_name"])
            index.upsert(
                Level.TABLE,
                idv,
                logical_name=logical,
                physical_name=physical,
            )


def load_graph(
    relations_csv: str,
    *,
    screens_csv: str | None = None,
    reports_csv: str | None = None,
    tables_csv: str | None = None,
    options: LoadOptions | None = None,
) -> TraceGraph:
    """Load CSV sources and build a populated :class:`TraceGraph`."""
    opts = options or LoadOptions()
    g = TraceGraph(index=NodeIndex())
    _load_screen_report_master(g, Level.SCREEN, screens_csv, opts)
    _load_screen_report_master(g, Level.REPORT, reports_csv, opts)
    _load_table_master(g, tables_csv, opts)

    with Path(relations_csv).open("r", encoding=opts.encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=opts.delimiter)
        headers = reader.fieldnames or []
        cols = _resolve_columns(
            headers,
            [
                "subsystem_id",
                "subsystem_name",
                "business_id",
                "business_name",
                "function_id",
                "function_name",
                "program_id",
                "program_name",
                "screen_id",
                "report_id",
                "table_id",
                "crud",
            ],
        )
        idx = g.index
        for row in reader:
            ss_id = _get(row, cols["subsystem_id"])
            ss_nm = _get(row, cols["subsystem_name"])
            bu_id = _get(row, cols["business_id"])
            bu_nm = _get(row, cols["business_name"])
            fn_id = _get(row, cols["function_id"])
            fn_nm = _get(row, cols["function_name"])
            pg_id = _get(row, cols["program_id"])
            pg_nm = _get(row, cols["program_name"])

            ss = _upsert_optional(idx, Level.SUBSYSTEM, ss_id, ss_nm)
            bu = _upsert_optional(idx, Level.BUSINESS, bu_id, bu_nm)
            fn = _upsert_optional(idx, Level.FUNCTION, fn_id, fn_nm)
            pg = _upsert_optional(idx, Level.PROGRAM, pg_id, pg_nm)

            g.add_hierarchy_chain(ss, bu, fn, pg)

            sc_id = _get(row, cols["screen_id"])
            rp_id = _get(row, cols["report_id"])
            tb_id = _get(row, cols["table_id"])
            crud = parse_crud(_get(row, cols["crud"]))

            if sc_id:
                sc = idx.upsert(Level.SCREEN, sc_id)
                if pg:
                    g.add_screen(pg, sc)
            if rp_id:
                rp = idx.upsert(Level.REPORT, rp_id)
                if pg:
                    g.add_report(pg, rp)
            if tb_id:
                tb = idx.upsert(Level.TABLE, tb_id)
                if pg:
                    g.add_crud(pg, tb, crud)
    return g
