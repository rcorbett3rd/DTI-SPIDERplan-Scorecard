"""Reusable disease-profile helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from .base import MetricDefinition, StructureDefinition


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json_config(path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON configuration file with a clear error message."""

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Required SPIDERplan configuration file was not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in SPIDERplan configuration file {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return data


def normalize_structure_name(name: str) -> str:
    """Normalize common DICOM structure-name punctuation and spacing."""

    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def structure_tokens(name: str) -> tuple[str, ...]:
    normalized = normalize_structure_name(name)
    return tuple(token for token in normalized.split("_") if token)


def contains_any(name: str, fragments: Iterable[str]) -> bool:
    normalized = normalize_structure_name(name)
    return any(normalize_structure_name(fragment) in normalized for fragment in fragments)


def alias_matches(name: str, alias: str) -> bool:
    """Match aliases conservatively while tolerating common delimiters."""

    normalized_name = normalize_structure_name(name)
    normalized_alias = normalize_structure_name(alias)
    if not normalized_alias:
        return False

    if normalized_name == normalized_alias:
        return True

    name_tokens = set(structure_tokens(normalized_name))
    alias_tokens = structure_tokens(normalized_alias)
    if len(alias_tokens) == 1 and alias_tokens[0] in name_tokens:
        return True

    return normalized_alias in normalized_name


def metric_from_mapping(mapping: Mapping[str, Any]) -> MetricDefinition:
    """Translate a JSON/config mapping into the shared metric model."""

    metric_type = str(mapping.get("type") or mapping.get("metric") or "").strip()
    if not metric_type:
        raise ValueError(f"Metric definition is missing a type: {mapping!r}")

    raw_limit = mapping.get("limit", mapping.get("preferred"))
    if raw_limit is None:
        raise ValueError(f"Metric definition is missing a limit: {mapping!r}")

    return MetricDefinition(
        metric_type=metric_type,
        limit=float(raw_limit),
        dose_gy=(
            None if mapping.get("dose_gy") is None else float(mapping["dose_gy"])
        ),
        preferred=(
            None if mapping.get("preferred") is None else float(mapping["preferred"])
        ),
        acceptable=(
            None
            if mapping.get("acceptable") is None
            else float(mapping["acceptable"])
        ),
        ideal=None if mapping.get("ideal") is None else float(mapping["ideal"]),
        units=mapping.get("units"),
        label=mapping.get("label"),
        weight=float(mapping.get("weight", 1.0)),
        metadata={
            key: value
            for key, value in mapping.items()
            if key
            not in {
                "type",
                "metric",
                "limit",
                "dose_gy",
                "preferred",
                "acceptable",
                "ideal",
                "units",
                "label",
                "weight",
            }
        },
    )


def structures_from_prostate_config(
    config: Mapping[str, Any],
) -> tuple[StructureDefinition, ...]:
    """Translate the current finalized Prostate OAR configuration."""

    raw_oars = config.get("oars", {})
    structures: list[StructureDefinition] = []

    for canonical_name, definition in raw_oars.items():
        aliases = tuple(
            dict.fromkeys(
                [
                    str(canonical_name),
                    *[str(alias) for alias in definition.get("aliases", [])],
                ]
            )
        )
        metrics = tuple(
            metric_from_mapping(metric)
            for metric in definition.get("metrics", [])
        )
        structures.append(
            StructureDefinition(
                canonical_name=str(canonical_name),
                aliases=aliases,
                metrics=metrics,
                category="OAR",
            )
        )

    return tuple(structures)
