"""General-purpose helpers that do not contain clinical scoring logic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROOT_DIR = Path(__file__).resolve().parent.parent


def project_path(*parts: str) -> Path:
    """Return a path relative to the repository root."""

    return ROOT_DIR.joinpath(*parts)


def safe_filename(value: str, fallback: str = "export") -> str:
    """Convert user- or DICOM-provided text into a safe filename stem."""

    cleaned = "".join(
        character if character.isalnum() or character in {"-", "_", "."} else "_"
        for character in str(value).strip()
    )
    cleaned = cleaned.strip("._")
    return cleaned or fallback


def stable_digest(parts: Iterable[Any]) -> str:
    """Create a deterministic digest suitable for cache keys."""

    payload = json.dumps(
        list(parts),
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
