"""Shared text-normalisation helpers used across layers."""

from __future__ import annotations

import re
import unicodedata

ID_RE = re.compile(r"^[A-Za-z0-9_]+$")


def nfkc_lower(s: str | None) -> str | None:
    """Return the NFKC-normalised, lower-cased string."""
    if s is None:
        return None
    t = unicodedata.normalize("NFKC", str(s)).strip()
    return t.lower() if t else None


def is_id_like(s: str) -> bool:
    """Check whether the given string resembles an identifier."""
    return bool(ID_RE.fullmatch(unicodedata.normalize("NFKC", str(s)).strip()))


def parse_crud(s: str | None) -> list[str]:
    """Parse CRUD operation tokens from a string."""
    if not s:
        return []
    raw = unicodedata.normalize("NFKC", str(s)).upper()
    raw = raw.replace(";", ",").replace("/", ",").replace("|", ",").replace(" ", "")
    initial = list(dict.fromkeys(ch for ch in raw if ch in {"C", "R", "U", "D"}))
    cs = list(initial)
    for token in (part.strip() for part in raw.split(",")):
        if token in {"C", "R", "U", "D"} and token not in cs:
            cs.append(token)
    return cs
