"""Unit tests for :mod:`tracability.domain.graph` normal flows."""

from __future__ import annotations

from tracability.domain import Level, NodeIndex, TraceGraph


def test_trace_hierarchy_from_subsystem_to_program() -> None:
    """Trace hierarchy chain SS -> BIZ -> FN -> PG."""
    idx = NodeIndex()
    ss = idx.upsert(Level.SUBSYSTEM, "SS1", logical_name="受注")
    biz = idx.upsert(Level.BUSINESS, "BIZ1", logical_name="受注業務")
    fn = idx.upsert(Level.FUNCTION, "FN1", logical_name="受注登録機能")
    pg = idx.upsert(Level.PROGRAM, "PG1", logical_name="受注登録PG")

    g = TraceGraph(idx)
    g.add_hierarchy_chain(ss, biz, fn, pg)

    results = g.trace(Level.SUBSYSTEM, Level.PROGRAM, "SS1", include_path=True)

    assert len(results) == 1
    r = results[0]
    assert r.node.id == "PG1"
    assert r.crud is None
    assert len(r.path) == 3
    assert all(step[1] == "hierarchy" for step in r.path)


def test_trace_program_to_screen_and_table_crud_forward() -> None:
    """Trace from program to screen and table via forward edges."""
    idx = NodeIndex()
    pg = idx.upsert(Level.PROGRAM, "PG1", logical_name="受注登録PG")
    sc = idx.upsert(Level.SCREEN, "SC1", logical_name="受注登録画面")
    tb = idx.upsert(Level.TABLE, "TB1", physical_name="orders")

    g = TraceGraph(idx)
    g.add_screen(pg, sc)
    g.add_crud(pg, tb, ["C", "R", "U"])  # forward CRUD

    # Program -> Screen
    res_screen = g.trace(Level.PROGRAM, Level.SCREEN, "PG1", include_path=True)
    assert len(res_screen) == 1
    rs = res_screen[0]
    assert rs.node.id == "SC1"
    assert rs.crud is None
    assert len(rs.path) == 1
    assert rs.path[0][1] == "screen"

    # Program -> Table (CRUD forward)
    res_table = g.trace(Level.PROGRAM, Level.TABLE, "PG1", include_path=True)
    assert len(res_table) == 1
    rt = res_table[0]
    assert rt.node.id == "TB1"
    assert rt.crud == {"C", "R", "U"}
    assert len(rt.path) == 1
    assert rt.path[0][1] == "crud"


def test_trace_table_to_program_and_screen_via_reverse_crud() -> None:
    """Trace starting from TABLE allows reverse CRUD, then forward edges."""
    idx = NodeIndex()
    pg = idx.upsert(Level.PROGRAM, "PG1")
    sc = idx.upsert(Level.SCREEN, "SC1")
    tb = idx.upsert(Level.TABLE, "TB1")

    g = TraceGraph(idx)
    g.add_screen(pg, sc)
    g.add_crud(pg, tb, ["C", "R"])  # CRUD edge PG -> TB

    # Starting from TABLE, reverse CRUD should be traversable
    res_pg = g.trace(Level.TABLE, Level.PROGRAM, "TB1", include_path=True)
    assert len(res_pg) == 1
    rpg = res_pg[0]
    assert rpg.node.id == "PG1"
    assert rpg.crud == {"C", "R"}
    assert len(rpg.path) == 1
    assert rpg.path[0][1] == "crud"

    # TABLE -> SCREEN through PROGRAM (reverse CRUD then forward SCREEN)
    res_sc = g.trace(Level.TABLE, Level.SCREEN, "TB1", include_path=True)
    assert len(res_sc) == 1
    rsc = res_sc[0]
    assert rsc.node.id == "SC1"
    assert rsc.crud == {"C", "R"}
    assert len(rsc.path) == 2
    assert rsc.path[0][1] == "crud"
    assert rsc.path[1][1] == "screen"
