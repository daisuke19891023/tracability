"""A lightweight YAML shim for environments without PyYAML.

This module implements a minimal subset of the PyYAML API used by the test
suite. It provides :func:`dump`, :func:`safe_dump`, and :func:`safe_load`, as
well as :class:`YAMLError`. Internally it serializes data as JSON, which is a
valid subset for the YAML structures exercised in the tests. The goal is not to
be feature complete but to offer predictable behaviour without requiring the
PyYAML dependency at runtime.
"""

from __future__ import annotations

import json
from typing import Any, IO, cast

__all__ = ["YAMLError", "dump", "safe_dump", "safe_load"]


class YAMLError(ValueError):
    """Exception raised for YAML parsing or serialization errors."""


def _ensure_text(stream: str | bytes | IO[str] | IO[bytes]) -> str:
    if hasattr(stream, "read"):
        readable = cast("IO[str] | IO[bytes]", stream)
        data = readable.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data
    if isinstance(stream, bytes):
        return stream.decode("utf-8")
    return str(stream)


def safe_load(stream: str | bytes | IO[str] | IO[bytes]) -> Any:
    """Parse YAML content from *stream*.

    The implementation accepts a subset compatible with JSON. Invalid content
    raises :class:`YAMLError` to mimic :mod:`yaml`'s behaviour.
    """
    text = _ensure_text(stream)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised via tests
        raise YAMLError(str(exc)) from exc


def dump(
    data: Any,
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool = False,
    allow_unicode: bool = True,
    sort_keys: bool = False,
    **_: Any,
) -> str | None:
    """Serialize *data* to YAML.

    The returned representation is JSON-formatted text, which is a valid YAML
    subset. Unsupported data types raise :class:`YAMLError`.
    """
    indent = None if default_flow_style else 2
    try:
        text = json.dumps(
            data,
            ensure_ascii=not allow_unicode,
            indent=indent,
            sort_keys=sort_keys,
        )
    except (TypeError, ValueError) as exc:  # pragma: no cover - dependent on input
        raise YAMLError(str(exc)) from exc

    if stream is not None:
        stream.write(text)
        return None
    return text


def safe_dump(
    data: Any,
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool = False,
    allow_unicode: bool = True,
    sort_keys: bool = False,
    **kwargs: Any,
) -> str | None:
    """Alias for :func:`dump` matching the PyYAML API."""
    return dump(
        data,
        stream,
        default_flow_style=default_flow_style,
        allow_unicode=allow_unicode,
        sort_keys=sort_keys,
        **kwargs,
    )
