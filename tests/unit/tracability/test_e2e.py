"""End-to-end tests for the traceability workflow."""

import textwrap
from pathlib import Path

from tracability import Level, TraceabilityService


def write(p: Path, name: str, content: str) -> None:
    """Write fixture content to ``tmp_path``."""
    (p / name).write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_end_to_end(tmp_path: Path) -> None:
    """Verify cross-level lookups via the service."""
    write(
        tmp_path,
        "relations.csv",
        """
        サブシステムID,サブシステム名,業務ID,業務名,機能ID,機能名,プログラムID,プログラム名,画面ID,帳票ID,テーブルID,CRUD
        SS01,受注,BU01,受注管理,FN10,受注登録,PRG100,受注登録画面,SC100,,T_ORDERS,CRU
        SS01,受注,BU01,受注管理,FN11,受注照会,PRG110,受注検索,SC110,RP110,T_ORDERS,R
        SS01,受注,BU01,受注管理,FN11,受注照会,PRG111,受注詳細,SC111,RP111,T_ORDER_LINES,R
        """,
    )
    write(
        tmp_path,
        "screens.csv",
        """
        screen_id,機能ID,画面名,物理名
        SC100,FN10,受注入力,ORDERS_ENTRY
        SC110,FN11,受注検索,ORDERS_SEARCH
        SC111,FN11,受注詳細,ORDERS_DETAIL
        """,
    )
    write(
        tmp_path,
        "reports.csv",
        """
        report_id,機能ID,帳票名,物理名
        RP110,FN11,受注一覧,ORDERS_LIST
        RP111,FN11,受注詳細,ORDERS_DETAIL_RPT
        """,
    )
    write(
        tmp_path,
        "tables.csv",
        """
        table_id,テーブル名,物理名
        T_ORDERS,受注ヘッダ,ORDERS
        T_ORDER_LINES,受注明細,ORDER_LINES
        """,
    )

    svc = TraceabilityService.from_files(
        relations_csv=str(tmp_path / "relations.csv"),
        screens_csv=str(tmp_path / "screens.csv"),
        reports_csv=str(tmp_path / "reports.csv"),
        tables_csv=str(tmp_path / "tables.csv"),
    )

    s_to_f = svc.query("screen", "function", "SC110", fmt="list")
    assert s_to_f
    assert s_to_f[0]["id"] == "FN11"

    f_to_s = svc.query("機能", "画面", "受注照会", by="name", fmt="list")
    got = sorted([x["id"] for x in f_to_s])
    assert got == ["SC110", "SC111"]

    p_to_b = svc.query(Level.PROGRAM, Level.BUSINESS, "PRG100", fmt="list")
    assert p_to_b
    assert p_to_b[0]["id"] == "BU01"

    r_to_b = svc.query("report", "business", "ORDERS_LIST", by="name", fmt="list")
    assert r_to_b
    assert r_to_b[0]["id"] == "BU01"

    p_to_t = svc.query("program", "table", "PRG100", relations={"crud"}, fmt="list")
    assert p_to_t
    assert p_to_t[0]["id"] == "T_ORDERS"
    crud_values = p_to_t[0]["crud"]
    assert crud_values is not None
    assert set(crud_values) == {"C", "R", "U"}
