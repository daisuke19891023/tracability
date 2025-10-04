"""Data models for traceability graph components."""

"""Domain models defining traceability nodes and levels."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Level(str, Enum):
    """Enumeration of supported traceability levels."""

    SUBSYSTEM = "subsystem"
    BUSINESS = "business"
    FUNCTION = "function"
    PROGRAM = "program"
    SCREEN = "screen"
    REPORT = "report"
    TABLE = "table"

    @classmethod
    def parse(cls, s: str) -> Level:
        """Parse various aliases into a :class:`Level` value."""
        key = str(s).strip().lower()
        aliases = {
            "subsystem": cls.SUBSYSTEM,
            "ss": cls.SUBSYSTEM,
            "サブシステム": cls.SUBSYSTEM,
            "business": cls.BUSINESS,
            "biz": cls.BUSINESS,
            "業務": cls.BUSINESS,
            "function": cls.FUNCTION,
            "fn": cls.FUNCTION,
            "機能": cls.FUNCTION,
            "program": cls.PROGRAM,
            "pgm": cls.PROGRAM,
            "プログラム": cls.PROGRAM,
            "screen": cls.SCREEN,
            "ui": cls.SCREEN,
            "画面": cls.SCREEN,
            "report": cls.REPORT,
            "rp": cls.REPORT,
            "帳票": cls.REPORT,
            "table": cls.TABLE,
            "db": cls.TABLE,
            "テーブル": cls.TABLE,
        }
        if key in aliases:
            return aliases[key]
        for alias_key, level in aliases.items():
            if alias_key in key:
                return level
        message = f"Unknown level: {s}"
        raise ValueError(message)


class Node(BaseModel):
    """Representation of an entity within the traceability graph."""

    model_config = ConfigDict(validate_assignment=True)
    level: Level
    id: str = Field(..., description="alphanumeric id")
    logical_name: str | None = None
    physical_name: str | None = None
    aliases: set[str] = Field(default_factory=set)

    @field_validator("id")
    @classmethod
    def _strip_id(cls, v: str) -> str:
        v = str(v).strip()
        if not v:
            message = "id is empty"
            raise ValueError(message)
        return v

    def key(self) -> tuple[Level, str]:
        """Return the index key for the node."""
        return (self.level, self.id)

    def label(self) -> str:
        """Compose a human-readable label for the node."""
        if self.logical_name and self.logical_name.strip():
            return f"{self.id} ({self.logical_name})"
        if (
            self.physical_name
            and self.physical_name.strip()
            and self.physical_name != self.id
        ):
            return f"{self.id} [{self.physical_name}]"
        return self.id
