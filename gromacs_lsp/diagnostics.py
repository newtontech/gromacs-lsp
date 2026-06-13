from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    file: str
    line: int
    column: int = 1
    evidence: list[str] = field(default_factory=list)
    suggested_fix: dict[str, Any] | None = None
    confidence: float = 1.0
    # OpenQC rule identity (stable, manifest-backed). None for legacy-only
    # diagnostics that have not yet been promoted to a first-class rule.
    rule_id: str | None = None
    manual_ref: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)
