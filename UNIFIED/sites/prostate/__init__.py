"""Finalized Prostate disease adapter."""

from __future__ import annotations

from typing import Sequence

from sites.base import MetricDefinition, SiteProfile
from sites.common import (
    alias_matches,
    load_json_config,
    normalize_structure_name,
    repository_root,
    structures_from_prostate_config,
)


_CONFIG_PATH = repository_root() / "prostate_config.json"
_CONFIG = load_json_config(_CONFIG_PATH)
_STRUCTURES = structures_from_prostate_config(_CONFIG)

PROFILE = SiteProfile(
    key="prostate",
    display_name="Prostate",
    config_path=_CONFIG_PATH,
    target_keywords=("ptv", "ctv", "gtv"),
    ignored_prefixes=("z",),
    ignored_suffixes=("opti",),
    eval_suffix="_eval",
    standard_prescriptions_gy={
        str(key): float(value)
        for key, value in _CONFIG.get("standard_prescriptions_gy", {}).items()
    },
    structures=_STRUCTURES,
    metadata={
        "site_label": _CONFIG.get("site", "Prostate"),
        "target_defaults": _CONFIG.get("target_defaults", {}),
        "muf": _CONFIG.get("muf", {}),
    },
)


def is_eval_target(name: str) -> bool:
    return normalize_structure_name(name).endswith(PROFILE.eval_suffix)


def is_target(name: str) -> bool:
    normalized = normalize_structure_name(name)
    if not normalized:
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
