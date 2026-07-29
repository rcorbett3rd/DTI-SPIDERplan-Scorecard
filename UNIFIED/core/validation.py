"""Shared validation helpers for uploaded DICOM plan groups."""

from __future__ import annotations

from typing import Any, Iterable

from .models import ProcessingIssue


REQUIRED_RT_MODALITIES = ("RTPLAN", "RTSTRUCT", "RTDOSE")


def validate_uploaded_files(files: Iterable[Any] | None) -> list[ProcessingIssue]:
    """Validate that at least one upload was supplied.

    Modality-specific validation remains in the DICOM engines because the
    existing Prostate and Head & Neck loaders use different input pathways.
    """

    uploaded = list(files or [])
    if uploaded:
        return []

    return [
        ProcessingIssue(
            level="warning",
            code="NO_UPLOADS",
            message="Please upload the RTPLAN, RTSTRUCT, and RTDOSE files.",
        )
    ]


def missing_modalities(found_modalities: Iterable[str]) -> list[str]:
    """Return required RT modalities that are absent."""

    normalized = {str(value).upper() for value in found_modalities}
    return [item for item in REQUIRED_RT_MODALITIES if item not in normalized]


def validate_required_modalities(
    found_modalities: Iterable[str],
) -> list[ProcessingIssue]:
    """Create a structured issue when required DICOM objects are missing."""

    missing = missing_modalities(found_modalities)
    if not missing:
        return []

    return [
        ProcessingIssue(
            level="error",
            code="MISSING_DICOM",
            message="Missing required DICOM object(s): " + ", ".join(missing),
            context={"missing_modalities": missing},
        )
    ]
