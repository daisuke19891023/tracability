# pyright: reportMissingModuleSource=false
"""Graph implementation for traceability relationships."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tracability.domain.index import NodeIndex, NodeKey
from tracability.domain.models import Level, Node

PathEntry = tuple[NodeKey, str, NodeKey]
State = tuple[NodeKey, list[PathEntry], set[str]]
TracePathStep = tuple[Node, str, Node]

if TYPE_CHECKING:  # pragma: no cover - optional dependency typing
    import networkx as nx


def _new_str_set() -> set[str]:
    return set()


@dataclass(slots=True)
class EdgeMeta:
    """Metadata describing an edge between two nodes."""

    relation: str
    crud: set[str] = field(default_factory=_new_str_set)


@dataclass(slots=True)
class TraceResult:
    """BFS traversal result for a destination node."""

    node: Node
    crud: set[str] | None
    path: list[TracePathStep]


class TraceGraph:
    """Directed graph representing traceability relationships."""

    def __init__(self, index: NodeIndex | None = None) -> None:
        """Create a graph bound to the provided node index."""
        self.index = index or NodeIndex()
        self._fwd: dict[NodeKey, dict[NodeKey, EdgeMeta]] = defaultdict(dict)
        self._rev: dict[NodeKey, dict[NodeKey, EdgeMeta]] = defaultdict(dict)

    def link(
        self,
        src: Node,
        dst: Node,
        relation: str,
        crud_ops: Iterable[str] | None = None,
    ) -> None:
        """Create or update an edge between two nodes."""
        src_key, dst_key = src.key(), dst.key()
        meta = self._fwd[src_key].get(dst_key)
        if meta is None:
            meta = EdgeMeta(relation=relation)
            self._fwd[src_key][dst_key] = meta
            self._rev[dst_key][src_key] = meta
        if relation == "crud" and crud_ops:
            meta.crud.update(c for c in crud_ops if c)

    def add_hierarchy_chain(
        self,
        ss: Node | None,
        bu: Node | None,
        fn: Node | None,
        pg: Node | None,
    ) -> None:
        """Link nodes along the subsystem→program hierarchy."""
        chain = [ss, bu, fn, pg]
        for i in range(len(chain) - 1):
            a, b = chain[i], chain[i + 1]
            if a and b:
                self.link(a, b, "hierarchy")

    def add_screen(self, src: Node, sc: Node) -> None:
        """Connect a function or program to a screen node."""
        self.link(src, sc, "screen")

    def add_report(self, src: Node, rp: Node) -> None:
        """Connect a function or program to a report node."""
        self.link(src, rp, "report")

    def add_crud(
        self,
        pg: Node | None,
        tb: Node | None,
        ops: Iterable[str] | None,
    ) -> None:
        """Register CRUD relationships between a program and a table."""
        if pg and tb:
            self.link(pg, tb, "crud", ops)

    def _neighbors(
        self,
        key: NodeKey,
        relations: set[str],
        direction: str,
        allow_reverse_crud: bool,
    ) -> Iterator[tuple[NodeKey, EdgeMeta]]:
        if direction in {"both", "forward"}:
            for nxt_key, meta in self._fwd.get(key, {}).items():
                if meta.relation in relations:
                    yield nxt_key, meta
        if direction in {"both", "reverse"}:
            for nxt_key, meta in self._rev.get(key, {}).items():
                if meta.relation in relations:
                    if meta.relation == "crud" and not allow_reverse_crud:
                        continue
                    yield nxt_key, meta

    def _start_nodes(self, level: Level, target: str, by: str) -> list[Node]:
        if by == "id":
            n = self.index.find_by_id(level, target)
            return [n] if n else []
        if by == "name":
            return (
                self.index.find_by_logical_name(level, target)
                or self.index.find_by_physical_name(level, target)
                or self.index.find_by_alias(level, target)
            )
        return self.index.find_auto(level, target, prefer="id")

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
        """Perform a bounded breadth-first search between two levels."""
        if relations is None:
            relations = {"hierarchy", "screen", "report", "crud"}
        starts = self._start_nodes(from_level, target, by)
        if not starts:
            return []

        queue: deque[State] = deque()
        seen: set[NodeKey] = self._enqueue_starts(starts, queue)
        start_keys = {node.key() for node in starts}
        results: list[TraceResult] = []
        allow_reverse_crud = from_level == Level.TABLE

        depth = 0
        while queue and depth <= max_depth:
            self._traverse_level(
                queue,
                results,
                seen,
                relations,
                direction,
                include_path,
                from_level,
                start_keys,
                to_level,
                allow_reverse_crud,
            )
            depth += 1

        return self._deduplicate_results(results)

    def _enqueue_starts(
        self,
        starts: list[Node],
        queue: deque[State],
    ) -> set[NodeKey]:
        seen: set[NodeKey] = set()
        for node in starts:
            key = node.key()
            queue.append((key, [], set()))
            seen.add(key)
        return seen

    def _traverse_level(
        self,
        queue: deque[State],
        results: list[TraceResult],
        seen: set[NodeKey],
        relations: set[str],
        direction: str,
        include_path: bool,
        from_level: Level,
        start_keys: set[NodeKey],
        to_level: Level,
        allow_reverse_crud: bool,
    ) -> None:
        for _ in range(len(queue)):
            current_key, path, crud_acc = queue.popleft()
            current_node = self.index.get_by_key(current_key)
            self._maybe_record_result(
                current_node,
                path,
                crud_acc,
                include_path,
                results,
                to_level,
            )
            for nxt_key, meta in self._neighbors(
                current_key,
                relations,
                direction,
                allow_reverse_crud,
            ):
                self._enqueue_neighbor(
                    current_key,
                    path,
                    crud_acc,
                    nxt_key,
                    meta,
                    queue,
                    seen,
                    from_level,
                    start_keys,
                )

    def _maybe_record_result(
        self,
        node: Node,
        path: list[PathEntry],
        crud_acc: set[str],
        include_path: bool,
        results: list[TraceResult],
        to_level: Level,
    ) -> None:
        if node.level != to_level or not path:
            return
        path_nodes: list[TracePathStep] = []
        if include_path:
            path_nodes = [
                (
                    self.index.get_by_key(src_key),
                    relation,
                    self.index.get_by_key(dst_key),
                )
                for (src_key, relation, dst_key) in path
            ]
        results.append(
            TraceResult(
                node=node,
                crud=set(crud_acc) if crud_acc else None,
                path=path_nodes,
            )
        )

    def _enqueue_neighbor(
        self,
        current_key: NodeKey,
        path: list[PathEntry],
        crud_acc: set[str],
        nxt_key: NodeKey,
        meta: EdgeMeta,
        queue: deque[State],
        seen: set[NodeKey],
        from_level: Level,
        start_keys: set[NodeKey],
    ) -> None:
        nxt_node = self.index.get_by_key(nxt_key)
        if nxt_node.level == from_level and nxt_key not in start_keys:
            return
        if nxt_key in seen:
            return
        seen.add(nxt_key)
        next_path = [*path, (current_key, meta.relation, nxt_key)]
        next_crud = set(crud_acc)
        if meta.relation == "crud" and meta.crud:
            next_crud.update(meta.crud)
        queue.append((nxt_key, next_path, next_crud))

    def _deduplicate_results(self, results: list[TraceResult]) -> list[TraceResult]:
        unique: dict[NodeKey, TraceResult] = {}
        for result in results:
            key = result.node.key()
            if key not in unique:
                unique[key] = result
        return list(unique.values())

    def to_networkx(self) -> "nx.DiGraph":
        """Export the graph to a :mod:`networkx` ``DiGraph`` instance."""
        try:
            import networkx as nx
        except ImportError as e:  # pragma: no cover - optional dependency
            message = "networkx が未インストールです。`pip install networkx`"
            raise RuntimeError(message) from e
        digraph = nx.DiGraph()
        for key, node in self.index.iter_nodes():
            digraph.add_node(
                key,
                level=node.level.value,
                id=node.id,
                logical_name=node.logical_name,
                physical_name=node.physical_name,
            )
        for s, adjs in self._fwd.items():
            for d, meta in adjs.items():
                digraph.add_edge(
                    s,
                    d,
                    relation=meta.relation,
                    crud=sorted(meta.crud) if meta.crud else None,
                )
        return digraph
