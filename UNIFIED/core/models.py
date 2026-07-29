"""Small shared data models used by site-independent infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlanIdentity:
    """Display-level plan identity independent of disease site."""

    label: str = "Unnamed Plan"
    name: str = ""
    fractions: int | None = None
    prescription_gy: float | None = None


@dataclass(frozen=True)
class ProcessingIssue:
    """A structured error, warning, or informational processing message."""

    level: str
    message: str
    code: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Container for a processed plan and any issues produced along the way."""

    data: dict[str, Any] = field(default_factory=dict)
    issues: list[ProcessingIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.level == "error" for issue in self.issues)

    @property
    def warnings(self) -> list[ProcessingIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]
