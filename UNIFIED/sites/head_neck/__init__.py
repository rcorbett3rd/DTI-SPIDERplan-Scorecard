"""Head & Neck disease adapter containing clinical logic only."""

from __future__ import annotations

from typing import Sequence

from sites.base import MetricDefinition, SiteProfile
from sites.common import (
    alias_matches,
    load_json_config,
    normalize_structure_name,
    repository_root,
)

from .metrics import STRUCTURES


_CONFIG_PATH = repository_root() / "hn_scoring_config.json"
_CONFIG = load_json_config(_CONFIG_PATH)

PROFILE = SiteProfile(
    key="head_neck",
    display_name="Head & Neck",
    config_path=_CONFIG_PATH,
    target_keywords=tuple(
        str(value).lower()
        for value in _CONFIG.get("target_keywords", ("PTV", "CTV", "GTV"))
    ),
    ignored_prefixes=("z",),
    ignored_suffixes=("opti",),
    eval_suffix="_eval",
    standard_prescriptions_gy={
        "high": 70.0,
        "highest": 70.0,
        "boost": 70.0,
        "mid": 63.0,
        "intermediate": 63.0,
        "low": 56.0,
        "elective": 56.0,
    },
    domain_weights={
        str(key): float(value)
        for key, value in _CONFIG.get("domain_weights", {}).items()
    },
    structures=STRUCTURES,
    metadata={
        "prototype_note": _CONFIG.get("prototype_note", ""),
        "serial_oar_keywords": tuple(_CONFIG.get("serial_oar_keywords", ())),
        "priority_oars": tuple(_CONFIG.get("priority_oars", ())),
        "v105_eval_only": True,
        "exclude_ln_helpers": True,
        "exclude_body_external": True,
    },
)


def _is_ln_helper(name: str) -> bool:
    normalized = normalize_structure_name(name)
    tokens = set(normalized.split("_"))
    return "ln" in tokens or normalized.startswith("ln") or normalized.endswith("_ln")


def is_eval_target(name: str) -> bool:
    return normalize_structure_name(name).endswith(PROFILE.eval_suffix)


def is_target(name: str) -> bool:
    normalized = normalize_structure_name(name)
    if not normalized:
        return False
    if normalized in {"body", "external"} or normalized.startswith("external"):
        return False
    if _is_ln_helper(normalized):
        return False
    if any(normalized.startswith(prefix) for prefix in PROFILE.ignored_prefixes):
        return False
    if any(normalized.endswith(suffix) for suffix in PROFILE.ignored_suffixes):
        return False
    return any(keyword in normalized for keyword in PROFILE.target_keywords)


def canonical_oar_name(name: str) -> str | None:
    matches = [
        structure.canonical_name
        for structure in PROFILE.structures
        if any(alias_matches(name, alias) for alias in structure.aliases)
    ]
    return matches[0] if matches else None


def configured_metrics_for(name: str) -> Sequence[MetricDefinition]:
    canonical = canonical_oar_name(name)
    if canonical is None:
        return ()
    for structure in PROFILE.structures:
        if structure.canonical_name == canonical:
            return structure.metrics
    return ()


from .engine import evaluate_sampled_metrics

__all__ = [
    "PROFILE",
    "normalize_structure_name",
    "is_target",
    "is_eval_target",
    "canonical_oar_name",
    "configured_metrics_for",
    "evaluate_sampled_metrics",
]
