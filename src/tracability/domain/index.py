"""Index utilities for resolving :class:`~tracability.models.Node` objects."""

from __future__ import annotations

from collections import defaultdict

from tracability.domain.models import Level, Node
from tracability.shared.utils import is_id_like, nfkc_lower

NodeKey = tuple[Level, str]


class NodeIndex:
    """Index nodes by multiple attributes for quick lookup."""

    def __init__(self) -> None:
        """Initialise the internal lookup tables."""
        self._by_key: dict[NodeKey, Node] = {}
        self._by_level_id: dict[Level, dict[str, NodeKey]] = defaultdict(dict)
        self._by_level_logical: dict[Level, dict[str, set[NodeKey]]] = defaultdict(
            lambda: defaultdict(set),
        )
        self._by_level_physical: dict[Level, dict[str, set[NodeKey]]] = defaultdict(
            lambda: defaultdict(set),
        )
        self._aliases: dict[Level, dict[str, set[NodeKey]]] = defaultdict(
            lambda: defaultdict(set),
        )

    def upsert(
        self,
        level: Level,
        identifier: str,
        logical_name: str | None = None,
        physical_name: str | None = None,
        aliases: set[str] | None = None,
    ) -> Node:
        """Insert a new node or update an existing node."""
        key = (level, identifier)
        node = self._by_key.get(key)
        if node is None:
            node = Node(
                level=level,
                id=identifier,
                logical_name=logical_name,
                physical_name=physical_name,
                aliases=set(aliases or set()),
            )
            self._by_key[key] = node
            self._by_level_id[level][identifier] = key
            if node.logical_name:
                logical_key = nfkc_lower(node.logical_name)
                if logical_key is not None:
                    self._by_level_logical[level][logical_key].add(key)
            if node.physical_name:
                physical_key = nfkc_lower(node.physical_name)
                if physical_key is not None:
                    self._by_level_physical[level][physical_key].add(key)
            for alias in node.aliases:
                alias_key = nfkc_lower(alias)
                if alias_key is not None:
                    self._aliases[level][alias_key].add(key)
            return node
        self.rename(
            level,
            identifier,
            logical_name=logical_name,
            physical_name=physical_name,
        )
        if aliases:
            for a in aliases:
                if a and a not in node.aliases:
                    node.aliases.add(a)
                    alias_key = nfkc_lower(a)
                    if alias_key is not None:
                        self._aliases[level][alias_key].add(key)
        return self._by_key[key]

    def get(self, level: Level, identifier: str) -> Node | None:
        """Return a node by its level and identifier."""
        key = self._by_level_id.get(level, {}).get(identifier)
        return self._by_key.get(key) if key else None

    def rename(
        self,
        level: Level,
        identifier: str,
        logical_name: str | None = None,
        physical_name: str | None = None,
    ) -> None:
        """Update logical or physical names for a node."""
        key = (level, identifier)
        node = self._by_key.get(key)
        if node is None:
            return
        if logical_name and logical_name != node.logical_name:
            if node.logical_name:
                previous_key = nfkc_lower(node.logical_name)
                if previous_key is not None:
                    self._by_level_logical[level][previous_key].discard(key)
            node.logical_name = logical_name
            new_key = nfkc_lower(logical_name)
            if new_key is not None:
                self._by_level_logical[level][new_key].add(key)
        if physical_name and physical_name != node.physical_name:
            if node.physical_name:
                previous_key = nfkc_lower(node.physical_name)
                if previous_key is not None:
                    self._by_level_physical[level][previous_key].discard(key)
            node.physical_name = physical_name
            new_key = nfkc_lower(physical_name)
            if new_key is not None:
                self._by_level_physical[level][new_key].add(key)

    def _name_lookup(
        self,
        index: dict[str, set[NodeKey]],
        name: str,
        partial: bool,
    ) -> list[Node]:
        q = nfkc_lower(name) or ""
        keys: list[NodeKey] = []
        if q in index:
            keys.extend(index[q])
        if partial:
            for key, values in index.items():
                if q and q in key and key != q:
                    keys.extend(values)
        return [self._by_key[k] for k in dict.fromkeys(keys)]

    def find_by_id(self, level: Level, id_value: str) -> Node | None:
        """Find a node by its identifier."""
        return self.get(level, id_value)

    def find_by_logical_name(
        self,
        level: Level,
        name: str,
        partial: bool = True,
    ) -> list[Node]:
        """Find nodes by logical name, optionally allowing partial matches."""
        return self._name_lookup(self._by_level_logical[level], name, partial)

    def find_by_physical_name(
        self,
        level: Level,
        name: str,
        partial: bool = True,
    ) -> list[Node]:
        """Find nodes by physical name, optionally allowing partial matches."""
        return self._name_lookup(self._by_level_physical[level], name, partial)

    def find_by_alias(
        self,
        level: Level,
        name: str,
        partial: bool = True,
    ) -> list[Node]:
        """Find nodes by registered aliases."""
        return self._name_lookup(self._aliases[level], name, partial)

    def find_auto(self, level: Level, target: str, prefer: str = "id") -> list[Node]:
        """Automatically resolve a target string to nodes."""
        res: list[Node] = []
        if prefer == "id" and is_id_like(target):
            n = self.find_by_id(level, target)
            if n:
                return [n]
        mapping_options = (
            (self.find_by_logical_name, self._by_level_logical[level]),
            (self.find_by_physical_name, self._by_level_physical[level]),
            (self.find_by_alias, self._aliases[level]),
        )
        for _, mapping in mapping_options:
            exact = self._name_lookup(mapping, target, partial=False)
            if exact:
                return exact
        res.extend(self.find_by_logical_name(level, target, partial=True))
        res.extend(self.find_by_physical_name(level, target, partial=True))
        res.extend(self.find_by_alias(level, target, partial=True))
        if prefer == "id" and not res:
            for f in (self.find_by_logical_name, self.find_by_physical_name):
                res.extend(f(level, target, partial=False))
        uniq: list[Node] = []
        seen: set[NodeKey] = set()
        for candidate in res:
            key = candidate.key()
            if key not in seen:
                uniq.append(candidate)
                seen.add(key)
        return uniq

    def get_by_key(self, key: NodeKey) -> Node:
        """Return a node using its compound key."""
        return self._by_key[key]

    def iter_nodes(self) -> list[tuple[NodeKey, Node]]:
        """Return all indexed nodes as ``(key, node)`` tuples."""
        return list(self._by_key.items())
