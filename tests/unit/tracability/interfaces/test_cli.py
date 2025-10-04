"""Tests for the Typer-based trace command registration."""

from __future__ import annotations

import json
import textwrap
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from tracability.interfaces.cli import create_app

if TYPE_CHECKING:
    from pathlib import Path


def _write_csv(base: Path, name: str, content: str) -> None:
    (base / name).write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_trace_command_outputs_json(tmp_path: Path) -> None:
    """Ensure the CLI command loads CSV files and prints JSON when requested."""
    _write_csv(
        tmp_path,
        "relations.csv",
        """
        サブシステムID,サブシステム名,業務ID,業務名,機能ID,機能名,プログラムID,プログラム名,画面ID,帳票ID,テーブルID,CRUD
        SS01,受注,BU01,受注管理,FN11,受注照会,PRG110,受注検索,SC110,RP110,T_ORDERS,R
        """,
    )
    _write_csv(
        tmp_path,
        "screens.csv",
        """
        screen_id,機能ID,画面名,物理名
        SC110,FN11,受注検索,ORDERS_SEARCH
        """,
    )
    runner = CliRunner()
    app = create_app()
    result = runner.invoke(
        app,
        [
            "--relations",
            str(tmp_path / "relations.csv"),
            "--screens",
            str(tmp_path / "screens.csv"),
            "--from-level",
            "program",
            "--to-level",
            "screen",
            "--target",
            "PRG110",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    loaded = json.loads(result.stdout)
    assert loaded
    assert loaded[0]["id"] == "SC110"
