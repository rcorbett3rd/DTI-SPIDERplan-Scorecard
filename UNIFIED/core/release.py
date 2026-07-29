"""Release-candidate metadata and health checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import platform
import sys
from typing import Any

from .constants import APP_NAME, RELEASE_NAME, VERSION
from .release_validation import validate_repository


@dataclass(frozen=True)
class ReleaseHealth:
    application: str
    release: str
    version: str
    python_version: str
    platform: str
    repository_errors: int
    repository_warnings: int
    repository_info: int
    ready: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def release_health(root: str | Path) -> ReleaseHealth:
    items = validate_repository(root)
    errors = sum(item.level == "error" for item in items)
    warnings = sum(item.level == "warning" for item in items)
    info = sum(item.level == "info" for item in items)

    return ReleaseHealth(
        application=APP_NAME,
        release=RELEASE_NAME,
        version=VERSION,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        repository_errors=errors,
        repository_warnings=warnings,
        repository_info=info,
        ready=errors == 0,
    )
