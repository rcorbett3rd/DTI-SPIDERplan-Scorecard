"""Common treatment-site contracts.

These models describe disease-specific clinical metadata without containing UI,
DICOM parsing, DVH sampling, plotting, or reporting code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class MetricDefinition:
    """A configuration-level metric definition."""

    metric_type: str
    limit: float
    dose_gy: float | None = None
    preferred: float | None = None
    acceptable: float | None = None
    ideal: float | None = None
    units: str | None = None
    label: str | None = None
    weight: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructureDefinition:
    """Canonical structure name with aliases and configured metrics."""

    canonical_name: str
    aliases: tuple[str, ...]
    metrics: tuple[MetricDefinition, ...] = ()
    category: str = "OAR"
    required: bool = False


@dataclass(frozen=True)
class SiteProfile:
    """Static metadata and configuration for one treatment site."""

    key: str
    display_name: str
    config_path: Path
    target_keywords: tuple[str, ...]
    ignored_prefixes: tuple[str, ...] = ("z",)
    ignored_suffixes: tuple[str, ...] = ("opti",)
    eval_suffix: str = "_eval"
    standard_prescriptions_gy: Mapping[str, float] = field(default_factory=dict)
    domain_weights: Mapping[str, float] = field(default_factory=dict)
    structures: tuple[StructureDefinition, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class SiteAdapter(Protocol):
    """Protocol implemented by disease-site adapter modules."""

    PROFILE: SiteProfile

    def normalize_structure_name(self, name: str) -> str:
        ...

    def is_target(self, name: str) -> bool:
        ...

    def is_eval_target(self, name: str) -> bool:
        ...

    def canonical_oar_name(self, name: str) -> str | None:
        ...

    def configured_metrics_for(self, name: str) -> Sequence[MetricDefinition]:
        ...
