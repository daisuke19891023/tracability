"""Unit tests for the CSV infrastructure loader."""

from __future__ import annotations

import importlib.util

import pytest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

if importlib.util.find_spec("pydantic") is None:
    pytest.skip(  # type: ignore[attr-defined]
        "pydantic is required for CSV loader tests", allow_module_level=True,
    )

from tracability.domain.models import Level
from tracability.infrastructure.csv.loader import LoadOptions, load_graph


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_graph_builds_hierarchy_and_crud_relationships(tmp_path: Path) -> None:
    """Ensure relations CSV builds hierarchy edges and CRUD links."""
    relations_csv = tmp_path / "relations.csv"
    screens_csv = tmp_path / "screens.csv"
    tables_csv = tmp_path / "tables.csv"

    _write_csv(
        relations_csv,
        """
サブシステムID,サブシステム名,業務ID,業務名,機能ID,機能名,program_id,program_name,screen_id,report_id,table_id,crud
SS1,サブシステムA,BZ1,業務A,FN1,機能A,PG1,受注プログラム,SC1,,ORD_TABLE,"C,R,U"
""".strip(),
    )

    _write_csv(
        screens_csv,
        """
画面ID,論理名,物理名,機能ID
SC1,受注画面,ORDER_SCREEN,FN1
""".strip(),
    )

    _write_csv(
        tables_csv,
        """
物理名,論理名
ORD_TABLE,受注明細
""".strip(),
    )

    graph = load_graph(
        str(relations_csv),
        screens_csv=str(screens_csv),
        tables_csv=str(tables_csv),
    )

    idx = graph.index
    subsystem = idx.get(Level.SUBSYSTEM, "SS1")
    business = idx.get(Level.BUSINESS, "BZ1")
    function = idx.get(Level.FUNCTION, "FN1")
    program = idx.get(Level.PROGRAM, "PG1")
    screen = idx.get(Level.SCREEN, "SC1")
    table = idx.get(Level.TABLE, "ORD_TABLE")

    assert subsystem is not None
    assert subsystem.logical_name == "サブシステムA"
    assert business is not None
    assert business.logical_name == "業務A"
    assert function is not None
    assert function.logical_name == "機能A"
    assert program is not None
    assert program.logical_name == "受注プログラム"
    assert screen is not None
    assert screen.logical_name == "受注画面"
    assert table is not None
    assert table.logical_name == "受注明細"

    hierarchy_results = graph.trace(Level.SUBSYSTEM, Level.PROGRAM, "SS1", by="id")
    assert {res.node.id for res in hierarchy_results} == {"PG1"}

    screen_results = graph.trace(Level.PROGRAM, Level.SCREEN, "PG1", by="id")
    assert {res.node.id for res in screen_results} == {"SC1"}

    crud_results = graph.trace(Level.PROGRAM, Level.TABLE, "PG1", by="id")
    assert len(crud_results) == 1
    assert crud_results[0].node.id == "ORD_TABLE"
    assert crud_results[0].crud == {"C", "R", "U"}


def test_load_graph_respects_custom_options(tmp_path: Path) -> None:
    """The loader should honour custom delimiters and enrich table metadata."""
    relations_csv = tmp_path / "relations.csv"
    tables_csv = tmp_path / "tables.csv"

    _write_csv(
        relations_csv,
        """
subsystem_id;business_id;function_id;program_id;screen_id;report_id;table_id;crud
SYSX;BIZX;FUNCX;PGX;;;orders_table;"C;D"
""".strip(),
    )

    _write_csv(
        tables_csv,
        """
physical_name;logical_name
orders_table;Orders Table
""".strip(),
    )

    graph = load_graph(
        str(relations_csv),
        tables_csv=str(tables_csv),
        options=LoadOptions(delimiter=";"),
    )

    idx = graph.index
    program = idx.get(Level.PROGRAM, "PGX")
    table = idx.get(Level.TABLE, "orders_table")

    assert program is not None
    assert table is not None
    assert table.logical_name == "Orders Table"

    results = graph.trace(Level.PROGRAM, Level.TABLE, "PGX", by="id")
    assert len(results) == 1
    assert results[0].node.id == "orders_table"
    assert results[0].crud == {"C", "D"}
