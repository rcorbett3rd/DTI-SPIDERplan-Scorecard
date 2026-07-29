"""Shared prescription extraction and target-assignment helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable, Mapping, Sequence

from sites.common import normalize_structure_name


@dataclass(frozen=True)
class TargetPrescription:
    structure: str
    prescription_gy: float | None
    source: str
    confidence: str
    is_eval: bool = False


def finite_positive(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def dose_from_structure_name(name: str) -> float | None:
    """Extract a plausible radiotherapy dose in Gy from a structure name."""

    text = str(name).lower()

    four_digit = re.findall(r"(?<!\d)(\d{4})(?!\d)", text)
    for token in reversed(four_digit):
        value = float(token) / 100.0
        if 20.0 <= value <= 100.0:
            return value

    two_or_three_digit = re.findall(
        r"(?<!\d)(\d{2,3}(?:\.\d+)?)(?!\d)",
        text,
    )
    for token in reversed(two_or_three_digit):
        value = float(token)
        if 20.0 <= value <= 100.0:
            return value

    return None


def dose_from_semantic_label(
    name: str,
    semantic_doses: Mapping[str, float],
) -> float | None:
    normalized = normalize_structure_name(name)
    for token, value in semantic_doses.items():
        if normalize_structure_name(token) in normalized:
            return finite_positive(value)
    return None


def base_target_name(name: str, eval_suffix: str = "_eval") -> str:
    normalized = normalize_structure_name(name)
    normalized_suffix = normalize_structure_name(eval_suffix)
    if normalized.endswith(normalized_suffix):
        normalized = normalized[: -len(normalized_suffix)].rstrip("_")
    return normalized


def assign_target_prescriptions(
    structures: Iterable[str],
    *,
    is_target,
    is_eval_target,
    semantic_doses: Mapping[str, float] | None = None,
    plan_prescription_gy: float | None = None,
    eval_suffix: str = "_eval",
) -> list[TargetPrescription]:
    """Assign target prescriptions using names, semantics, and eval inheritance."""

    semantic_doses = semantic_doses or {}
    names = [str(name) for name in structures if is_target(str(name))]
    assignments: dict[str, TargetPrescription] = {}

    for name in names:
        numeric = dose_from_structure_name(name)
        semantic = dose_from_semantic_label(name, semantic_doses)

        if numeric is not None:
            assignments[name] = TargetPrescription(
                structure=name,
                prescription_gy=numeric,
                source="structure name",
                confidence="high",
                is_eval=is_eval_target(name),
            )
        elif semantic is not None:
            assignments[name] = TargetPrescription(
                structure=name,
                prescription_gy=semantic,
                source="semantic target label",
                confidence="medium",
                is_eval=is_eval_target(name),
            )

    # Eval structures inherit from the matching base target when they do not
    # contain their own explicit dose.
    by_base: dict[str, list[TargetPrescription]] = {}
    for assignment in assignments.values():
        by_base.setdefault(base_target_name(assignment.structure, eval_suffix), []).append(
            assignment
        )

    for name in names:
        if name in assignments or not is_eval_target(name):
            continue
        base = base_target_name(name, eval_suffix)
        possible = [
            item for item in by_base.get(base, [])
            if item.prescription_gy is not None and not item.is_eval
        ]
        if possible:
            inherited = possible[0]
            assignments[name] = TargetPrescription(
                structure=name,
                prescription_gy=inherited.prescription_gy,
                source=f"inherited from {inherited.structure}",
                confidence="high",
                is_eval=True,
            )

    unresolved = [name for name in names if name not in assignments]
    known_doses = sorted(
        {
            item.prescription_gy
            for item in assignments.values()
            if item.prescription_gy is not None
        },
        reverse=True,
    )

    fallback = finite_positive(plan_prescription_gy)
    for name in unresolved:
        if fallback is not None and len(known_doses) <= 1:
            assignments[name] = TargetPrescription(
                structure=name,
                prescription_gy=fallback,
                source="plan prescription",
                confidence="low",
                is_eval=is_eval_target(name),
            )
        else:
            assignments[name] = TargetPrescription(
                structure=name,
                prescription_gy=None,
                source="unresolved",
                confidence="none",
                is_eval=is_eval_target(name),
            )

    return [assignments[name] for name in names]


def highest_assigned_dose(
    assignments: Sequence[TargetPrescription],
) -> float | None:
    values = [
        item.prescription_gy
        for item in assignments
        if item.prescription_gy is not None
    ]
    return max(values) if values else None
