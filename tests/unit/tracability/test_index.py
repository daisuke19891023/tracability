"""Tests for the :mod:`tracability.domain.index` module."""

from tracability.domain import NodeIndex
from tracability.domain.models import Level


def test_alias_and_rename_and_auto() -> None:
    """Ensure NodeIndex resolves nodes via id, names, and aliases."""
    idx = NodeIndex()
    idx.upsert(Level.PROGRAM, "PRG1", logical_name="受注登録")
    assert idx.find_by_id(Level.PROGRAM, "PRG1") is not None

    idx.rename(Level.PROGRAM, "PRG1", logical_name="受注登録(改)")
    res = idx.find_by_logical_name(Level.PROGRAM, "受注登録(改)", partial=False)
    assert len(res) == 1
    assert res[0].id == "PRG1"

    idx.upsert(Level.PROGRAM, "PRG1", aliases={"ORDERS_ENTRY"})
    res2 = idx.find_by_alias(Level.PROGRAM, "ORDERS_ENTRY", partial=False)
    assert len(res2) == 1
    assert res2[0].id == "PRG1"

    auto = idx.find_auto(Level.PROGRAM, "PRG1")
    assert auto is not None
    assert auto[0].id == "PRG1"
